"""
session.py - Server-side session store.
Replaces st.session_state: config, dataset, model_manager, tracker keyed by session_id.
Dataset persisted to storage/sessions/{id}.parquet; config to storage/sessions/{id}.json.
"""
import json
import logging
import os
import threading
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

from backend.core.data_pipeline import DataPreprocessor
from backend.core.model_manager import ModelManager, ExperimentTracker

logger = logging.getLogger(__name__)

SESSIONS_DIR = os.path.join(os.getcwd(), "storage", "sessions")

DEFAULT_CONFIG: Dict[str, Any] = {
    "provider": "SumoPod",
    "model_name": "gpt-4o-mini",
    "base_url": "",
    "task_type": "classification",
    "data_source": "synthetic",
    "ai_description": "",
    "n_samples": 200,
    "n_features": 10,
    "max_iterations": 3,
    "target_column": None,
}


@dataclass
class Session:
    session_id: str
    config: Dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_CONFIG))
    dataset: Optional[pd.DataFrame] = None
    target: Optional[str] = None
    preprocessor: DataPreprocessor = field(default_factory=DataPreprocessor)
    model_manager: ModelManager = field(default_factory=ModelManager)
    tracker: ExperimentTracker = field(default_factory=ExperimentTracker)
    best_score: float = 0.0
    best_model_name: str = "None"
    agent_trace: List[str] = field(default_factory=list)
    iteration_results: List[Dict[str, Any]] = field(default_factory=list)
    agent_summary: str = ""
    agent_running: bool = False

    @property
    def data_path(self) -> str:
        return os.path.join(SESSIONS_DIR, f"{self.session_id}.csv")

    def set_dataset(self, df: pd.DataFrame, target: Optional[str]) -> None:
        self.dataset = df
        self.target = target
        os.makedirs(SESSIONS_DIR, exist_ok=True)
        df.to_csv(self.data_path, index=False)

    def preview(self, rows: int = 20) -> Dict[str, Any]:
        if self.dataset is None:
            return {"has_data": False}
        return {
            "has_data": True,
            "columns": list(self.dataset.columns),
            "dtypes": {c: str(t) for c, t in self.dataset.dtypes.items()},
            "shape": list(self.dataset.shape),
            "target": self.target,
            "rows": self.dataset.head(rows).to_dict(orient="records"),
        }


_store: Dict[str, Session] = {}
_lock = threading.Lock()


def create_session() -> Session:
    session_id = uuid.uuid4().hex[:12]
    session = Session(session_id=session_id)
    with _lock:
        _store[session_id] = session
    _persist_config(session)
    logger.info(f"Session created: {session_id}")
    return session


def get_session(session_id: str) -> Session:
    with _lock:
        session = _store.get(session_id)
    if session is None:
        raise KeyError(f"Unknown session: {session_id}")
    return session


def update_config(session: Session, patch: Dict[str, Any]) -> Dict[str, Any]:
    for key in DEFAULT_CONFIG:
        if key in patch:
            session.config[key] = patch[key]
    _persist_config(session)
    return session.config


def _persist_config(session: Session) -> None:
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    path = os.path.join(SESSIONS_DIR, f"{session.session_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"session_id": session.session_id, "config": session.config,
                   "target": session.target, "best_score": session.best_score,
                   "best_model_name": session.best_model_name}, f, indent=2)


def persist_session(session: Session) -> None:
    _persist_config(session)
    if session.dataset is not None and not os.path.exists(session.data_path):
        session.set_dataset(session.dataset, session.target)
