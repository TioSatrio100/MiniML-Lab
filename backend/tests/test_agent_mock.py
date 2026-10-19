"""
test_agent_mock.py — fake LLM (deterministic tool sequence) → SSE event order,
budget stop, cancel path.

Fake agent: instead of calling the real LangChain loop we drive Job/queue exactly
like routes_agent._run_agent does, using the real tools from make_tools() with a
stub context. This validates SSE contract + budget enforcement end to end without
network.
"""
import json
import os
import time

from langchain.tools import ToolRuntime

from backend.core.llm_agent import MLAgentContext, make_tools
from backend.core.model_manager import ModelManager, ExperimentTracker


def _fake_runtime():
    return ToolRuntime(state=None, context=None, config=None, stream_writer=lambda text: None, tool_call_id="test", store=None)


class _Writer:
    def __init__(self, job):
        self.job = job

    def __call__(self, text):
        self.job.push("progress", {"text": text})


def _mk_ctx(client, session_id, budget=2):
    from backend.core import session as session_store

    session = session_store.get_session(session_id)
    ctx = MLAgentContext(
        preprocessor=session.preprocessor,
        dataset=session.dataset,
        target=session.target,
        task="classification",
        model_manager=ModelManager(),
        tracker=ExperimentTracker(),
        data_path=session.data_path,
        budget=budget,
    )
    return session, ctx


def _read_sse(client, session_id, job_id, timeout=10):
    events = []
    with client.stream("GET", f"/api/session/{session_id}/agent/stream/{job_id}") as resp:
        assert resp.status_code == 200
        buffer = ""
        start = time.time()
        for chunk in resp.iter_text():
            buffer += chunk
            while "\n\n" in buffer:
                part, buffer = buffer.split("\n\n", 1)
                event, data = "", ""
                for line in part.split("\n"):
                    if line.startswith("event: "):
                        event = line[7:]
                    elif line.startswith("data: "):
                        data += line[6:]
                if event:
                    events.append((event, json.loads(data)))
            if time.time() - start > timeout:
                break
    return events


def test_tools_budget_exhaustion(client, session_id):
    """run_experiment refuses after budget spent — message, not crash."""
    session, ctx = _mk_ctx(client, session_id, budget=2)
    tools = {t.name: t for t in make_tools(ctx)}
    run_experiment = tools["run_experiment"]
    rt = _fake_runtime()

    good_code = "print('noop')"
    run_experiment.invoke({"code": good_code, "runtime": rt})
    run_experiment.invoke({"code": good_code, "runtime": rt})
    third = run_experiment.invoke({"code": good_code, "runtime": rt})

    # both fail (no metrics) but budget counts: third must be BUDGET_EXHAUSTED
    assert third.startswith("BUDGET_EXHAUSTED")
    assert ctx.budget_used == 2


def test_tools_syntax_error_then_failure(client, session_id):
    session, ctx = _mk_ctx(client, session_id, budget=3)
    tools = {t.name: t for t in make_tools(ctx)}
    rt = _fake_runtime()

    result = tools["run_experiment"].invoke({"code": "def broken(:", "runtime": rt})
    assert result.startswith("SYNTAX_ERROR")
    # failed iterations don't count best score
    assert ctx.best_score == 0.0


def test_run_experiment_success_updates_best(client, session_id):
    """Real sandbox run: trivial 'model' printing metrics + writing pkl file."""
    client.post(
        f"/api/session/{session_id}/data/synthetic",
        json={"task_type": "classification", "n_samples": 30, "n_features": 3},
    )
    session, ctx = _mk_ctx(client, session_id, budget=1)
    ctx.dataset = session.dataset
    tools = {t.name: t for t in make_tools(ctx)}
    rt = _fake_runtime()

    code = """
import os, pickle
print('METRICS_JSON: {"accuracy": 0.9123}')
pickle.dump(123, open('trained_model.pkl', 'wb'))
print('MODEL_PATH: trained_model.pkl')
"""
    result = tools["run_experiment"].invoke({"code": code, "runtime": rt})
    data = json.loads(result)
    assert data["status"] == "success"
    assert data["metrics"]["accuracy"] == 0.9123
    assert data["is_better"] is True
    assert ctx.best_score == 0.9123
    assert data["model_path"] and os.path.exists(data["model_path"])


def test_full_sse_contract_order(client, session_id):
    """POST run → GET stream: trace* → iteration* → done."""
    client.post(
        f"/api/session/{session_id}/data/synthetic",
        json={"task_type": "classification", "n_samples": 30, "n_features": 3},
    )
    resp = client.post(f"/api/session/{session_id}/agent/run")
    assert resp.status_code == 200, f"run failed: {resp.status_code} {resp.text}"
    job_id = resp.json()["job_id"]

    # run real worker (no LLM key → error path produces trace + error + done)
    events = _read_sse(client, session_id, job_id)
    kinds = [e for e, _ in events]

    assert kinds[-1] == "done", f"stream must end with done, got {kinds[-3:]}"
    assert "error" in kinds or "trace" in kinds

    done_data = dict(events)["done"]
    assert "summary" in done_data and "best_score" in done_data and "cancelled" in done_data

    # session released
    status = client.get(f"/api/session/{session_id}/status").json()
    assert status["agent_running"] is False


def test_cancel_mid_run(client, session_id):
    client.post(
        f"/api/session/{session_id}/data/synthetic",
        json={"task_type": "classification", "n_samples": 30, "n_features": 3},
    )
    run_resp = client.post(f"/api/session/{session_id}/agent/run").json()
    job_id = run_resp["job_id"]
    # give worker a beat, then cancel
    time.sleep(0.2)
    resp = client.post(f"/api/session/{session_id}/agent/cancel?job_id={job_id}")
    assert resp.status_code == 200

    # second run allowed after cancel (agent_running cleared)
    run2 = client.post(f"/api/session/{session_id}/agent/run")
    assert run2.status_code == 200
    # clean up: read/discard second stream
    _read_sse(client, session_id, run2.json()["job_id"], timeout=5)


def test_run_without_data_400(client):
    sid = client.post("/api/session").json()["session_id"]
    resp = client.post(f"/api/session/{sid}/agent/run")
    assert resp.status_code == 400
    assert "dataset" in resp.json()["detail"].lower()


def test_llm_failure_emits_error_then_done(client, session_id):
    """No API key configured → worker pushes error + done, releases agent_running."""
    client.post(
        f"/api/session/{session_id}/data/synthetic",
        json={"task_type": "classification", "n_samples": 30, "n_features": 4},
    )
    job_id = client.post(f"/api/session/{session_id}/agent/run").json()["job_id"]
    events = _read_sse(client, session_id, job_id)
    kinds = [e for e, _ in events]
    assert kinds[-1] == "done"
    assert "error" in kinds  # banner path
    assert "cancelled" in events[-1][1] and events[-1][1]["cancelled"] is False
    status = client.get(f"/api/session/{session_id}/status").json()
    assert status["agent_running"] is False  # button re-enable path


def test_multi_session_tracker_isolation(client):
    """Two sessions: experiment logged in A must not appear in B (9c)."""
    a = client.post("/api/session").json()["session_id"]
    b = client.post("/api/session").json()["session_id"]

    from backend.core import session as session_store

    ta = session_store.get_session(a).tracker
    ta.log_experiment(iteration=1, code="x", execution_time=0, success=True, metrics={"accuracy": 0.9})

    tb = session_store.get_session(b).tracker
    assert tb.get_experiment_history() == []
    # and A still sees its own
    assert len(ta.get_experiment_history()) == 1
