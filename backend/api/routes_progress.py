"""
Experiment progress routes: history + Plotly chart JSON.
"""
import json
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from backend.core import session as session_store
from backend.core.visualization import create_training_progress_chart, get_task_metric

router = APIRouter(prefix="/api", tags=["progress"])


@router.get("/session/{session_id}/progress")
def progress(session_id: str) -> Dict[str, Any]:
    try:
        session = session_store.get_session(session_id)
    except KeyError:
        raise HTTPException(404, "Session not found")

    experiments = session.tracker.get_experiment_history()
    task = session.config.get("task_type", "classification")
    metric, metric_label, higher_is_better = get_task_metric(task)

    successful = [e for e in experiments if e.get("success")]
    scores = [e["metrics"].get(metric, 0) for e in successful]
    if scores:
        best = max(scores) if higher_is_better else min(scores)
        improvement = best - scores[0] if higher_is_better else scores[0] - best
    else:
        best, improvement = 0, 0

    fig = create_training_progress_chart(experiments, task)
    return {
        "experiments": experiments,
        "stats": {
            "total": len(experiments),
            "successful": len(successful),
            "metric": metric,
            "metric_label": metric_label,
            "best_score": best,
            "improvement": improvement,
            "best_score_so_far": session.best_score,
            "best_model_name": session.best_model_name,
        },
        "chart": json.loads(fig.to_json()),
    }
