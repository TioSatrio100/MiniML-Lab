"""
Provider registry routes — user-managed platforms (base_url + api_key + models).
api_key never returned to client.
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.core.providers import BUILTIN_TEMPLATES, ProviderRegistry

router = APIRouter(prefix="/api/providers", tags=["providers"])

registry = ProviderRegistry()


class ProviderCreate(BaseModel):
    name: str
    base_url: str = ""
    api_key: str = ""
    models: List[str] = []


class ProviderUpdate(BaseModel):
    base_url: Optional[str] = None
    api_key: Optional[str] = None


class ModelAdd(BaseModel):
    model: str


@router.get("")
def list_providers():
    return registry.list()


@router.post("")
def add_provider(body: ProviderCreate):
    if not body.name.strip():
        raise HTTPException(400, "Provider name required")
    try:
        return registry.add(body.name.strip(), body.base_url, body.api_key, body.models)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.patch("/{name}")
def update_provider(name: str, body: ProviderUpdate):
    try:
        return registry.update(name, body.base_url, body.api_key)
    except KeyError as e:
        raise HTTPException(404, str(e))


@router.post("/{name}/models")
def add_model(name: str, body: ModelAdd):
    try:
        models = registry.add_model(name, body.model)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"name": name, "models": models}


@router.delete("/{name}")
def remove_provider(name: str):
    if name in BUILTIN_TEMPLATES:
        raise HTTPException(400, "Built-in provider cannot be deleted (edit instead)")
    registry.remove(name)
    return {"removed": name}


@router.delete("/{name}/models/{model:path}")
def remove_model(name: str, model: str):
    try:
        models = registry.remove_model(name, model)
    except KeyError as e:
        raise HTTPException(404, str(e))
    return {"name": name, "models": models}


@router.post("/{name}/discovery")
async def discovery(name: str):
    try:
        models = await registry.fetch_models(name)
        return {"name": name, "models": models}
    except Exception as e:
        raise HTTPException(502, f"Model discovery failed: {e}")
