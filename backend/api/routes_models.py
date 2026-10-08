"""
Model artifact routes: list, best, download, code.
"""
import json
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.core.model_manager import ModelManager
from backend.core.visualization import get_task_metric

router = APIRouter(prefix="/api/models", tags=["models"])

_manager: Optional[ModelManager] = None


def get_manager() -> ModelManager:
    global _manager
    if _manager is None:
        _manager = ModelManager()
    return _manager


@router.get("")
def list_models() -> Any:
    return get_manager().list_models()


@router.get("/best")
def best_model(task: str = "classification") -> Any:
    metric, _, higher_is_better = get_task_metric(task)
    model = get_manager().get_best_model(metric, higher_is_better)
    if model is None:
        raise HTTPException(404, "No saved models")
    return model


@router.get("/{model_name}/download")
def download(model_name: str) -> FileResponse:
    for model in get_manager().list_models():
        if model["model_name"] == model_name:
            path = model["artifacts"].get("model")
            if path and os.path.exists(path):
                return FileResponse(path, filename=os.path.basename(path), media_type="application/octet-stream")
    raise HTTPException(404, "Model not found")


@router.get("/{model_name}/code")
def get_code(model_name: str) -> Dict[str, Any]:
    for model in get_manager().list_models():
        if model["model_name"] == model_name:
            path = model["artifacts"].get("code")
            if path and os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return {"model_name": model_name, "code": f.read()}
            raise HTTPException(404, "No code artifact for this model")
    raise HTTPException(404, "Model not found")


@router.get("/{model_name}/metadata")
def get_metadata(model_name: str) -> Dict[str, Any]:
    for model in get_manager().list_models():
        if model["model_name"] == model_name:
            path = model["artifacts"].get("metadata")
            if path and os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            raise HTTPException(404, "No metadata artifact")
    raise HTTPException(404, "Model not found")
