"""
Agent routes: init, run job, SSE stream, cancel.
agent.stream() runs in a worker thread; chunks pushed to asyncio.Queue → SSE.
Event schema:
  message    {token}
  tool_call  {name, args}
  tool_result{name, content}
  progress   {text}          (runtime.stream_writer: "Executing experiment 1/3...")
  trace      {line}          (composed display line, mirrors old st.session_state.agent_trace)
  iteration  {status, metrics, model_path, is_better, best_score, error?}
  done       {summary, best_score, best_model_name, cancelled}
  error      {message}
"""
import asyncio
import json
import threading
import uuid
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.api.routes_models import get_manager
from backend.core import session as session_store
from backend.core.llm_agent import MLAgentContext, create_agent_with_tools
from backend.core.providers import get_model
from backend.core.visualization import get_task_metric

router = APIRouter(prefix="/api", tags=["agent"])


class Job:
    def __init__(self, session_id: str):
        self.job_id = uuid.uuid4().hex[:12]
        self.session_id = session_id
        self.queue: asyncio.Queue = asyncio.Queue()
        self.loop: asyncio.AbstractEventLoop | None = None
        self.cancelled = threading.Event()

    def push(self, event: str, data: Any) -> None:
        if self.loop is None:
            return
        self.loop.call_soon_threadsafe(self.queue.put_nowait, {"event": event, "data": data})


_jobs: Dict[str, Job] = {}


def _get_session(session_id: str) -> session_store.Session:
    try:
        return session_store.get_session(session_id)
    except KeyError:
        raise HTTPException(404, "Session not found")


@router.post("/session/{session_id}/agent/init")
def agent_init(session_id: str) -> Dict[str, Any]:
    session = _get_session(session_id)
    cfg = session.config
    try:
        get_model(cfg["provider"], cfg["model_name"])
    except ValueError as e:
        return {"ready": False, "error": str(e)}
    except Exception as e:
        return {"ready": False, "error": f"Model init failed: {e}"}
    return {"ready": True, "provider": cfg["provider"], "model": cfg["model_name"]}


@router.post("/session/{session_id}/agent/run")
async def agent_run(session_id: str) -> Dict[str, Any]:
    session = _get_session(session_id)
    if session.agent_running:
        raise HTTPException(409, "Agent already running")
    if session.dataset is None:
        raise HTTPException(400, "No dataset — prepare data first")

    job = Job(session_id)
    job.loop = asyncio.get_running_loop()
    _jobs[job.job_id] = job

    session.agent_running = True
    session.agent_trace = []
    session.iteration_results = []
    session.agent_summary = ""

    threading.Thread(target=_run_agent, args=(job, session), daemon=True).start()
    return {"job_id": job.job_id}


@router.get("/session/{session_id}/agent/stream/{job_id}")
async def agent_stream(session_id: str, job_id: str):
    session = _get_session(session_id)
    job = _jobs.get(job_id)
    if job is None or job.session_id != session_id:
        raise HTTPException(404, "Job not found")

    async def event_gen():
        try:
            while True:
                item = await job.queue.get()
                yield f"event: {item['event']}\ndata: {json.dumps(item['data'])}\n\n"
                if item["event"] == "done":
                    break
        finally:
            if not job.cancelled.is_set() and session.agent_running:
                job.cancelled.set()

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/session/{session_id}/agent/cancel")
def agent_cancel(session_id: str, job_id: str) -> Dict[str, Any]:
    session = _get_session(session_id)
    job = _jobs.get(job_id)
    if job:
        job.cancelled.set()
        job.push("done", {"summary": session.agent_summary, "best_score": session.best_score,
                          "best_model_name": session.best_model_name, "cancelled": True})
    session.agent_running = False
    return {"cancelled": True}


def _run_agent(job: Job, session: session_store.Session) -> None:
    """Worker thread: consume agent.stream(), push SSE events."""
    cfg = session.config
    ctx = None
    final_message = []

    def push(event: str, data: Any) -> None:
        job.push(event, data)

    def trace(line: str) -> None:
        session.agent_trace.append(line)
        push("trace", {"line": line})

    try:
        model = get_model(cfg["provider"], cfg["model_name"])
        ctx = MLAgentContext(
            preprocessor=session.preprocessor,
            dataset=session.dataset,
            target=session.target,
            task=cfg["task_type"],
            model_manager=get_manager(),
            tracker=session.tracker,
            data_path=session.data_path,
            budget=cfg["max_iterations"],
            best_score=session.best_score,
            best_model_name=session.best_model_name,
        )
        agent = create_agent_with_tools(model, ctx)

        stream = agent.stream(
            {"messages": [{"role": "user", "content": "Find the best model for my data"}]},
            stream_mode=["updates", "messages", "custom"],
            version="v2",
        )

        for chunk in stream:
            if job.cancelled.is_set():
                break

            ctype = chunk.get("type")

            if ctype == "messages":
                token, _meta = chunk["data"]
                if hasattr(token, "content") and token.content:
                    final_message.append(token.content)
                    push("message", {"token": token.content})
                    trace(f"💭 {token.content[:80]}")

            elif ctype == "updates":
                for node, update in chunk["data"].items():
                    if node == "tools":
                        for msg in update.get("messages", []):
                            content = getattr(msg, "content", "")
                            name = getattr(msg, "name", "tool")
                            push("tool_result", {"name": name, "content": str(content)[:500]})
                            trace(f"🔧 {name}: {str(content)[:100]}")
                            if name == "run_experiment":
                                _handle_iteration(session, content, push, trace)
                    elif node == "model":
                        for msg in update.get("messages", []):
                            for tc in getattr(msg, "tool_calls", None) or []:
                                push("tool_call", {"name": tc.get("name"), "args": tc.get("args", {})})
                                trace(f"🧠 Calling: {tc.get('name')}({str(tc.get('args'))[:60]})")

            elif ctype == "custom":
                text = chunk["data"]
                push("progress", {"text": text})
                trace(f"⚡ {text}")

    except Exception as e:
        trace(f"❌ Error: {e}")
        push("error", {"message": str(e)})
    finally:
        cancelled = job.cancelled.is_set()
        session.agent_running = False
        if ctx is not None:
            session.best_score = ctx.best_score
            session.best_model_name = ctx.best_model_name

        summary = ""
        if final_message:
            summary = "".join(final_message)[:500]
        elif ctx is not None and ctx.history:
            metric, metric_label, _ = get_task_metric(ctx.task)
            summary = f"Completed {ctx.budget_used} iterations. Best {metric_label}: {ctx.best_score:.4f} (model: {ctx.best_model_name})"
        session.agent_summary = summary

        push("done", {
            "summary": summary,
            "best_score": session.best_score,
            "best_model_name": session.best_model_name,
            "cancelled": cancelled,
        })


def _handle_iteration(session: session_store.Session, content: Any, push, trace) -> None:
    """run_experiment returns JSON on success, error string otherwise."""
    text = str(content)
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        data = None

    if isinstance(data, dict) and data.get("status") == "success":
        session.iteration_results.append(data)
        push("iteration", data)
    else:
        err = {"status": "failed", "error": text[:300]}
        if text.startswith(("BUDGET_EXHAUSTED", "SYNTAX_ERROR", "FAILED", "NO_METRICS", "TIMEOUT", "ERROR")):
            session.iteration_results.append(err)
            push("iteration", err)
