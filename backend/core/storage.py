"""
storage.py - JSON file persistence for model registry and experiment history.
"""
import json
import logging
import os
import threading
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

STORAGE_DIR = os.path.join(os.getcwd(), "storage")
MODELS_FILE = os.path.join(STORAGE_DIR, "models.json")
EXPERIMENTS_FILE = os.path.join(STORAGE_DIR, "experiments.json")

_lock = threading.Lock()


def _read(path: str, default: Any) -> Any:
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read {path}: {e}")
        return default


def _write(path: str, data: Any) -> None:
    os.makedirs(STORAGE_DIR, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def load_models() -> Dict[str, Dict]:
    with _lock:
        return _read(MODELS_FILE, {})


def save_models(models: Dict[str, Dict]) -> None:
    with _lock:
        _write(MODELS_FILE, models)


def load_experiments(session_id: Optional[str] = None) -> List[Dict]:
    with _lock:
        return _read(_experiments_path(session_id), [])


def save_experiments(experiments: List[Dict], session_id: Optional[str] = None) -> None:
    with _lock:
        path = _experiments_path(session_id)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        _write(path, experiments)


def _experiments_path(session_id: Optional[str]) -> str:
    """Per-session experiment history — prevents tracker bleed between sessions."""
    if not session_id:
        return EXPERIMENTS_FILE
    return os.path.join(STORAGE_DIR, "experiments", f"{session_id}.json")
