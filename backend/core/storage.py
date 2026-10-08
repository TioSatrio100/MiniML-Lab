"""
storage.py - JSON file persistence for model registry and experiment history.
"""
import json
import logging
import os
import threading
from typing import Any, Dict, List

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


def load_experiments() -> List[Dict]:
    with _lock:
        return _read(EXPERIMENTS_FILE, [])


def save_experiments(experiments: List[Dict]) -> None:
    with _lock:
        _write(EXPERIMENTS_FILE, experiments)
