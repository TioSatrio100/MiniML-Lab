"""
Session, config, and data routes.
"""
from typing import Any, Dict, Optional

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from backend.core import session as session_store
from backend.core.data_pipeline import DataPreprocessor

router = APIRouter(prefix="/api", tags=["session-data"])


class ConfigPatch(BaseModel):
    provider: Optional[str] = None
    model_name: Optional[str] = None
    base_url: Optional[str] = None
    task_type: Optional[str] = None
    data_source: Optional[str] = None
    ai_description: Optional[str] = None
    n_samples: Optional[int] = None
    n_features: Optional[int] = None
    max_iterations: Optional[int] = None
    target_column: Optional[str] = None


class SyntheticRequest(BaseModel):
    task_type: str
    n_samples: int
    n_features: int


def _get(session_id: str) -> session_store.Session:
    try:
        return session_store.get_session(session_id)
    except KeyError:
        raise HTTPException(404, "Session not found")


@router.post("/session")
def create_session() -> Dict[str, Any]:
    session = session_store.create_session()
    return {"session_id": session.session_id, "config": session.config}


@router.get("/session/{session_id}/config")
def get_config(session_id: str) -> Dict[str, Any]:
    return _get(session_id).config


@router.put("/session/{session_id}/config")
def put_config(session_id: str, patch: ConfigPatch) -> Dict[str, Any]:
    session = _get(session_id)
    return session_store.update_config(session, patch.model_dump(exclude_none=True))


@router.post("/session/{session_id}/data/synthetic")
def generate_synthetic(session_id: str, body: SyntheticRequest) -> Dict[str, Any]:
    session = _get(session_id)
    prep = DataPreprocessor()
    try:
        df = prep.generate_synthetic_data(body.task_type, body.n_samples, body.n_features)
    except ValueError as e:
        raise HTTPException(400, str(e))
    target = "target" if body.task_type in ("classification", "regression") else None
    session.preprocessor = prep
    session.set_dataset(df, target)
    session_store.update_config(session, {"task_type": body.task_type})
    return {"preview": session.preview()}


@router.post("/session/{session_id}/data/csv")
async def upload_csv(session_id: str, file: UploadFile = File(...), target_column: Optional[str] = None) -> Dict[str, Any]:
    session = _get(session_id)
    content = await file.read()
    prep = DataPreprocessor()
    try:
        df, target = prep.load_csv_data(content, target_column)
    except Exception as e:
        raise HTTPException(400, f"CSV load failed: {e}")
    session.preprocessor = prep
    session.set_dataset(df, target)
    session_store.update_config(session, {"target_column": target})
    return {"preview": session.preview()}


@router.get("/session/{session_id}/data/preview")
def data_preview(session_id: str) -> Dict[str, Any]:
    return _get(session_id).preview()


@router.get("/session/{session_id}/status")
def session_status(session_id: str) -> Dict[str, Any]:
    session = _get(session_id)
    return {
        "has_data": session.dataset is not None,
        "target": session.target,
        "config": session.config,
        "best_score": session.best_score,
        "best_model_name": session.best_model_name,
        "agent_running": session.agent_running,
        "agent_trace": session.agent_trace[-20:],
        "iteration_results": session.iteration_results,
        "agent_summary": session.agent_summary,
    }
