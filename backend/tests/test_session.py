"""
test_session.py — session create/config roundtrip + data-source restriction (7c).
"""
from backend.core.session import ConfigValidationError


def test_create_session(client):
    resp = client.post("/api/session")
    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"]
    assert body["config"]["task_type"] == "classification"
    assert body["config"]["data_source"] == "synthetic"


def test_config_roundtrip(client, session_id):
    resp = client.put(
        f"/api/session/{session_id}/config",
        json={"task_type": "regression", "max_iterations": 5, "n_samples": 300},
    )
    assert resp.status_code == 200
    cfg = resp.json()
    assert cfg["task_type"] == "regression"
    assert cfg["max_iterations"] == 5
    assert cfg["n_samples"] == 300

    # persisted + fetched back
    fetched = client.get(f"/api/session/{session_id}/config").json()
    assert fetched == cfg


def test_config_partial_patch_keeps_other_fields(client, session_id):
    client.put(f"/api/session/{session_id}/config", json={"max_iterations": 7})
    cfg = client.put(f"/api/session/{session_id}/config", json={"n_samples": 111}).json()
    assert cfg["max_iterations"] == 7
    assert cfg["n_samples"] == 111


def test_unknown_session_404(client):
    assert client.get("/api/session/doesnotexist/config").status_code == 404


def test_reject_synthetic_clustering(client, session_id):
    resp = client.put(
        f"/api/session/{session_id}/config",
        json={"task_type": "clustering", "data_source": "synthetic"},
    )
    assert resp.status_code == 400
    # config untouched
    cfg = client.get(f"/api/session/{session_id}/config").json()
    assert cfg["task_type"] == "classification"


def test_reject_synthetic_recommendation_after_regression(client, session_id):
    client.put(f"/api/session/{session_id}/config", json={"task_type": "regression"})
    resp = client.put(f"/api/session/{session_id}/config", json={"task_type": "recommendation"})
    assert resp.status_code == 400


def test_clustering_allowed_after_csv(session_id, client):
    csv = "a,b,rating\n1,2,4.0\n3,4,2.0\n5,6,5.0\n"
    resp = client.post(
        f"/api/session/{session_id}/data/csv",
        files={"file": ("d.csv", csv.encode())},
        params={"target_column": "rating"},
    )
    assert resp.status_code == 200
    resp = client.put(f"/api/session/{session_id}/config", json={"task_type": "clustering"})
    assert resp.status_code == 200
