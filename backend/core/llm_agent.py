"""
llm_agent.py - LangChain-based Autonomous ML Agent
Tool-calling agent that generates, executes, and iterates ML experiments.
"""
import os
import re
import json
import shutil
import logging
import subprocess
import tempfile
import pickle
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from langchain.tools import tool, ToolRuntime
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage

logger = logging.getLogger(__name__)

STAGING_DIR = os.path.join(os.getcwd(), "models", "staging")
os.makedirs(STAGING_DIR, exist_ok=True)


@dataclass
class MLAgentContext:
    preprocessor: Any
    dataset: Any
    target: Optional[str]
    task: str
    model_manager: Any
    tracker: Any
    data_path: str
    budget: int = 3
    budget_used: int = 0
    best_score: float = 0.0
    best_model_name: str = "None"
    history: List[Dict[str, Any]] = field(default_factory=list)


def make_tools(ctx: MLAgentContext):
    @tool
    def analyze_dataset() -> str:
        """Analyze the current dataset and return summary (shape, features, target, missing values, dtypes)."""
        info = ctx.preprocessor.analyze_data(ctx.dataset, ctx.target, ctx.task)
        return info.data_summary

    @tool
    def run_experiment(code: str, runtime: ToolRuntime) -> str:
        """Execute ML training code in a sandboxed subprocess. Code must load data from DATA_PATH env var,
        save model as 'trained_model.pkl', and print METRICS_JSON: {...} and MODEL_PATH: trained_model.pkl at the end.
        Returns metrics JSON on success or truncated error on failure."""
        if ctx.budget_used >= ctx.budget:
            return "BUDGET_EXHAUSTED: No more iterations allowed. Call save_model and finish."
        ctx.budget_used += 1
        writer = runtime.stream_writer
        writer(f"Executing experiment {ctx.budget_used}/{ctx.budget}...")

        code = code.strip()
        if code.startswith("```python"):
            code = code[9:]
        elif code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]
        code = code.strip()

        try:
            import ast
            ast.parse(code)
        except SyntaxError as e:
            writer(f"Experiment {ctx.budget_used} SYNTAX ERROR")
            ctx.history.append({"status": "syntax_error", "error": str(e)})
            return f"SYNTAX_ERROR at line {e.lineno}: {e.msg}. Fix the code and retry."

        temp_dir = tempfile.mkdtemp()
        script_path = os.path.join(temp_dir, "exp.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)

        try:
            from backend.sandbox import run_script
            process = run_script(script_path, temp_dir, ctx.data_path, timeout=120)
            output = process.stdout
            error = process.stderr if process.returncode != 0 else None

            if process.returncode != 0:
                writer(f"Experiment {ctx.budget_used} FAILED")
                error_msg = (error or output or "Unknown error")[:800]
                result = {"status": "failed", "error": error_msg}
                ctx.history.append(result)
                ctx.tracker.log_experiment(
                    iteration=ctx.budget_used,
                    code=code,
                    execution_time=0,
                    success=False,
                    error=error_msg,
                )
                return f"FAILED (exit code {process.returncode}): {error_msg}"

            metrics = _parse_metrics(output)
            temp_model_path = _extract_model_path(output, temp_dir)

            staging_model_path = None
            if temp_model_path and os.path.exists(temp_model_path):
                staging_model_path = os.path.join(STAGING_DIR, f"iter_{ctx.budget_used}_model.pkl")
                shutil.copy2(temp_model_path, staging_model_path)
                staging_code_path = os.path.join(STAGING_DIR, f"iter_{ctx.budget_used}_code.py")
                with open(staging_code_path, "w", encoding="utf-8") as f:
                    f.write(code)

            if metrics is None:
                writer(f"Experiment {ctx.budget_used} — no metrics parsed")
                result = {"status": "no_metrics", "output": output[:300]}
                ctx.history.append(result)
                return f"NO_METRICS: Could not parse METRICS_JSON from output. Output: {output[:300]}"

            from backend.core.visualization import get_task_metric
            metric, metric_label, higher_is_better = get_task_metric(ctx.task)
            current_score = metrics.get(metric, 0)
            is_better = (
                (current_score > ctx.best_score)
                if higher_is_better
                else (current_score < ctx.best_score and current_score > 0)
            )
            if is_better:
                ctx.best_score = current_score

            best_tag = " NEW_BEST" if is_better else ""
            writer(f"Experiment {ctx.budget_used} — {metric_label}={current_score:.4f}{best_tag}")

            ctx.history.append({
                "status": "success",
                "metrics": metrics,
                "model_path": staging_model_path,
                "code_path": staging_code_path if staging_model_path else None,
                "is_better": is_better,
            })
            ctx.tracker.log_experiment(
                iteration=ctx.budget_used,
                code=code,
                execution_time=0,
                success=True,
                metrics=metrics,
                model_path=staging_model_path,
            )

            return json.dumps({
                "status": "success",
                "metrics": metrics,
                "model_path": staging_model_path,
                "is_better": is_better,
                "best_score": ctx.best_score,
            })

        except subprocess.TimeoutExpired:
            writer(f"Experiment {ctx.budget_used} TIMEOUT")
            ctx.history.append({"status": "timeout"})
            return "TIMEOUT: Code execution exceeded 120 seconds."
        except Exception as e:
            writer(f"Experiment {ctx.budget_used} ERROR: {e}")
            ctx.history.append({"status": "error", "error": str(e)})
            return f"ERROR: {str(e)}"

    @tool
    def get_history() -> str:
        """Get experiment history: best score so far and all iteration results with metrics/errors."""
        if not ctx.history:
            return "No experiments run yet. Start with analyze_dataset, then generate and run code."
        lines = [f"Best score so far: {ctx.best_score:.4f}"]
        for i, h in enumerate(ctx.history, 1):
            if h["status"] == "success":
                metrics_str = ", ".join(f"{k}={v:.4f}" for k, v in h["metrics"].items())
                best_flag = " ★ BEST" if h.get("is_better") else ""
                lines.append(f"Iter {i}: SUCCESS — {metrics_str}{best_flag}")
            else:
                err = h.get("error", h.get("status", "unknown"))
                lines.append(f"Iter {i}: {h['status'].upper()} — {str(err)[:150]}")
        lines.append("\nStrategy: Beat the best score. If errors occurred, fix them.")
        return "\n".join(lines)

    @tool
    def save_model(name: str) -> str:
        """Save the current best model to artifacts. Call after run_experiment returns is_better=true."""
        last_success = None
        for h in reversed(ctx.history):
            if h.get("status") == "success" and h.get("model_path"):
                last_success = h
                break
        if not last_success:
            return "No successful experiment with saved model file to save."

        model_path = last_success["model_path"]
        if not os.path.exists(model_path):
            return f"Model file not found at {model_path}"

        code = ""
        code_path = last_success.get("code_path")
        if code_path and os.path.exists(code_path):
            with open(code_path, "r", encoding="utf-8") as f:
                code = f.read()

        try:
            with open(model_path, "rb") as f:
                model_obj = pickle.load(f)
            artifacts = ctx.model_manager.save_model(
                model=model_obj,
                name=name,
                metrics=last_success["metrics"],
                code=code,
            )
            ctx.best_model_name = name
            return f"Saved as '{name}'. Artifacts: {list(artifacts.keys())}"
        except Exception as e:
            return f"Save failed: {e}"

    @tool
    def finish(summary: str) -> str:
        """End the Auto-ML loop with a final summary of results."""
        return summary

    return [analyze_dataset, run_experiment, get_history, save_model, finish]


def _parse_metrics(output: str) -> Optional[Dict[str, Any]]:
    if not output:
        return None
    try:
        matches = re.findall(
            r'\{[^{}]*(?:"accuracy"|"r2"|"rmse"|"silhouette_score"|"mae"|"precision_at_k"|"precision"|"recall"|"f1"|"inertia"|"n_clusters")[^{}]*\}',
            output,
        )
        if matches:
            return json.loads(matches[-1])
    except Exception:
        pass
    return None


def _extract_model_path(output: str, base_dir: str) -> Optional[str]:
    for line in output.splitlines():
        if line.startswith("MODEL_PATH:"):
            return os.path.join(base_dir, line.replace("MODEL_PATH:", "").strip())
    return None


SYSTEM_PROMPTS = {
    "classification": """You are an autonomous ML agent for CLASSIFICATION tasks.

WORKFLOW:
1. Call analyze_dataset to understand the data.
2. Generate COMPLETE Python training code that:
   - Loads data from os.environ['DATA_PATH'] using pandas
   - Preprocesses (handle missing values, encode categoricals, scale features)
   - Splits train/test (stratified)
   - Trains a model (try RandomForest, GradientBoosting, SVM, XGBoost)
   - Saves model as 'trained_model.pkl' using pickle
   - Prints METRICS_JSON: {"accuracy": val, "precision": val, "recall": val, "f1": val}
   - Prints MODEL_PATH: trained_model.pkl
3. Call run_experiment with the COMPLETE code.
4. If is_better=true, call save_model with a descriptive name.
5. If accuracy < 0.85, try different algorithms or preprocessing.
6. Call get_history to review past attempts.
7. When done (or budget exhausted), call finish with summary.

CRITICAL: Generate COMPLETE, executable Python code. No markdown blocks. No truncation. All imports at top. All code must run without errors.""",

    "regression": """You are an autonomous ML agent for REGRESSION tasks.

WORKFLOW:
1. Call analyze_dataset to understand the data.
2. Generate COMPLETE Python training code that:
   - Loads data from os.environ['DATA_PATH'] using pandas
   - Preprocesses (handle missing values, encode categoricals, scale features)
   - Splits train/test
   - Trains a model (try LinearRegression, Ridge, RandomForestRegressor, GradientBoostingRegressor)
   - Saves model as 'trained_model.pkl' using pickle
   - Prints METRICS_JSON: {"r2": val, "rmse": val, "mae": val}
   - Prints MODEL_PATH: trained_model.pkl
3. Call run_experiment with the COMPLETE code.
4. If is_better=true, call save_model with a descriptive name.
5. If R² < 0.8, try different algorithms or feature engineering.
6. Call get_history to review past attempts.
7. When done, call finish with summary.

CRITICAL: Generate COMPLETE, executable Python code. No markdown blocks. No truncation. All imports at top. All code must run without errors.""",

    "clustering": """You are an autonomous ML agent for CLUSTERING tasks (UNSUPERVISED — NO target column).

WORKFLOW:
1. Call analyze_dataset to understand the data.
2. Generate COMPLETE Python training code that:
   - Loads data from os.environ['DATA_PATH'] using pandas
   - Preprocesses (handle missing values, encode categoricals, scale features)
   - NO target column — this is unsupervised
   - Trains a clustering model (try KMeans, DBSCAN, AgglomerativeClustering)
   - Optimizes silhouette score by trying different cluster counts
   - Saves model as 'trained_model.pkl' using pickle
   - Prints METRICS_JSON: {"silhouette_score": val, "inertia": val, "n_clusters": val}
   - Prints MODEL_PATH: trained_model.pkl
3. Call run_experiment with the COMPLETE code.
4. If is_better=true, call save_model with a descriptive name.
5. Call get_history to review past attempts.
6. When done, call finish with summary.

CRITICAL: Generate COMPLETE, executable Python code. No markdown blocks. No truncation. All imports at top. All code must run without errors.""",

    "recommendation": """You are an autonomous ML agent for CONTENT-BASED RECOMMENDATION tasks.

WORKFLOW:
1. Call analyze_dataset to understand the data.
2. Generate COMPLETE Python training code that:
   - Loads data from os.environ['DATA_PATH'] using pandas
   - Builds a content-based recommendation system using item features
   - Uses cosine similarity or other similarity metrics
   - Evaluates using RMSE on predicted ratings
   - Saves model as 'trained_model.pkl' using pickle
   - Prints METRICS_JSON: {"rmse": val, "mae": val, "precision_at_k": val}
   - Prints MODEL_PATH: trained_model.pkl
3. Call run_experiment with the COMPLETE code.
4. If is_better=true, call save_model with a descriptive name.
5. Call get_history to review past attempts.
6. When done, call finish with summary.

CRITICAL: Generate COMPLETE, executable Python code. No markdown blocks. No truncation. All imports at top. All code must run without errors.""",
}


@wrap_tool_call
def handle_tool_errors(request, handler):
    try:
        return handler(request)
    except Exception as e:
        logger.error(f"Tool error: {e}")
        return ToolMessage(
            content=f"Tool error: {str(e)[:200]}. Please check your input and try again.",
            tool_call_id=request.tool_call["id"],
        )


def create_agent_with_tools(model, ctx: MLAgentContext):
    tools = make_tools(ctx)
    system_prompt = SYSTEM_PROMPTS.get(ctx.task, SYSTEM_PROMPTS["classification"])
    return create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        middleware=[handle_tool_errors],
    )
