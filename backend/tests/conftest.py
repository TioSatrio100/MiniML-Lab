"""
Shared fixtures: isolate cwd-dependent storage/models paths per test via
monkeypatched module constants (no reload — routes keep their references).
"""
import os
import tempfile

import pytest


@pytest.fixture()
def tmp_paths(monkeypatch):
    tmp = tempfile.mkdtemp(prefix="miniml_test_")
    storage_dir = os.path.join(tmp, "storage")
    sessions = os.path.join(storage_dir, "sessions")
    staging = os.path.join(tmp, "models", "staging")
    os.makedirs(sessions, exist_ok=True)
    os.makedirs(staging, exist_ok=True)

    import backend.core.llm_agent as llm_agent
    import backend.core.providers as providers
    import backend.core.session as session
    import backend.core.storage as storage
    import backend.core.model_manager as model_manager

    monkeypatch.setattr(providers, "PROVIDERS_FILE", os.path.join(storage_dir, "providers.json"))
    monkeypatch.setattr(providers, "STORAGE_DIR", storage_dir)
    monkeypatch.setattr(session, "SESSIONS_DIR", sessions)
    monkeypatch.setattr(llm_agent, "STAGING_DIR", staging)
    monkeypatch.setattr(storage, "STORAGE_DIR", storage_dir)
    monkeypatch.setattr(storage, "MODELS_FILE", os.path.join(storage_dir, "models.json"))
    monkeypatch.setattr(storage, "EXPERIMENTS_FILE", os.path.join(storage_dir, "experiments.json"))
    return {"tmp": tmp, "storage": storage_dir, "sessions": sessions, "staging": staging, "models": os.path.join(tmp, "models")}


@pytest.fixture()
def client(tmp_paths, monkeypatch):
    """TestClient + per-test isolation of session store and model manager."""
    import backend.api.routes_models as routes_models
    import backend.api.routes_agent as routes_agent
    from backend.core import session as session_store
    from fastapi.testclient import TestClient

    from backend.app import app

    monkeypatch.setattr(routes_models, "_manager", None)
    monkeypatch.setattr(session_store, "_store", {})
    monkeypatch.setattr(routes_agent, "_jobs", {})

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def session_id(client):
    resp = client.post("/api/session")
    assert resp.status_code == 200
    return resp.json()["session_id"]
