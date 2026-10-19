"""
test_providers.py — registry CRUD, key never leaked, builtin protection.
"""
import json
import os

import backend.core.providers as providers


def test_list_has_builtin_templates(client):
    items = client.get("/api/providers").json()
    names = {p["name"] for p in items}
    assert {"SumoPod", "OpenRouter", "OpenAI", "Ollama"} <= names
    for p in items:
        assert "api_key" not in p  # never leaked
        assert p["has_key"] is False


def test_add_provider_roundtrip(client):
    resp = client.post(
        "/api/providers",
        json={"name": "MyHost", "base_url": "http://localhost:9999/v1", "api_key": "sk-secret", "models": ["m1"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "MyHost"
    assert body["has_key"] is True
    assert "sk-secret" not in json.dumps(body)

    listed = {p["name"]: p for p in client.get("/api/providers").json()}
    assert listed["MyHost"]["has_key"] is True
    assert "api_key" not in listed["MyHost"]


def test_key_persisted_server_side_only(client, tmp_paths):
    client.post("/api/providers", json={"name": "K", "base_url": "http://x/v1", "api_key": "sk-abc"})
    raw = json.load(open(os.path.join(tmp_paths["storage"], "providers.json"), encoding="utf-8"))
    assert raw["K"]["api_key"] == "sk-abc"
    assert all("api_key" not in p for p in client.get("/api/providers").json())


def test_update_provider_key(client):
    client.post("/api/providers", json={"name": "U", "base_url": "http://x/v1", "api_key": "a"})
    resp = client.patch("/api/providers/U", json={"api_key": "b"})
    assert resp.status_code == 200
    assert resp.json()["has_key"] is True


def test_builtin_delete_protected(client):
    resp = client.delete("/api/providers/SumoPod")
    assert resp.status_code == 400


def test_custom_delete(client):
    client.post("/api/providers", json={"name": "D", "base_url": "http://x/v1"})
    assert client.delete("/api/providers/D").status_code == 200
    assert "D" not in {p["name"] for p in client.get("/api/providers").json()}


def test_add_model(client):
    resp = client.post("/api/providers/OpenAI/models", json={"model": "gpt-5"})
    assert resp.status_code == 200
    assert "gpt-5" in resp.json()["models"]


def test_get_model_requires_key():
    import pytest

    with pytest.raises(ValueError, match="No API key"):
        providers.get_model("OpenAI", "gpt-4o-mini")
