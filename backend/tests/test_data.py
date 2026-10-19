"""
test_data.py - synthetic gen, CSV upload + target detect, preview, AI-route validation.
"""


def test_synthetic_classification(client, session_id):
    resp = client.post(
        f"/api/session/{session_id}/data/synthetic",
        json={"task_type": "classification", "n_samples": 100, "n_features": 6},
    )
    assert resp.status_code == 200
    preview = resp.json()["preview"]
    assert preview["has_data"] is True
    assert preview["shape"] == [100, 7]  # + target col
    assert preview["target"] == "target"
    assert 0 < len(preview["rows"]) <= 20  # preview capped at 20


def test_synthetic_regression(client, session_id):
    resp = client.post(
        f"/api/session/{session_id}/data/synthetic",
        json={"task_type": "regression", "n_samples": 50, "n_features": 4},
    )
    assert resp.status_code == 200
    assert resp.json()["preview"]["target"] == "target"


def test_synthetic_clustering_blocked(client, session_id):
    resp = client.post(
        f"/api/session/{session_id}/data/synthetic",
        json={"task_type": "clustering", "n_samples": 50, "n_features": 4},
    )
    assert resp.status_code == 400
    assert "clustering" in resp.json()["detail"].lower()


def test_synthetic_recommendation_blocked(client, session_id):
    resp = client.post(
        f"/api/session/{session_id}/data/synthetic",
        json={"task_type": "recommendation", "n_samples": 50, "n_features": 4},
    )
    assert resp.status_code == 400


def test_csv_upload_auto_target(client, session_id):
    csv = "x,y,label\n1.0,2.0,cat\n3.0,4.0,dog\n5.0,6.0,cat\n"
    resp = client.post(f"/api/session/{session_id}/data/csv", files={"file": ("t.csv", csv.encode())})
    assert resp.status_code == 200
    preview = resp.json()["preview"]
    assert preview["target"] == "label"  # last column
    assert preview["shape"] == [3, 3]


def test_csv_upload_explicit_target(client, session_id):
    csv = "x,label,y\n1.0,cat,2.0\n3.0,dog,4.0\n"
    resp = client.post(
        f"/api/session/{session_id}/data/csv",
        files={"file": ("t.csv", csv.encode())},
        params={"target_column": "label"},
    )
    assert resp.status_code == 200
    assert resp.json()["preview"]["target"] == "label"


def test_csv_bad_target_400(client, session_id):
    csv = "x,y\n1,2\n"
    resp = client.post(
        f"/api/session/{session_id}/data/csv",
        files={"file": ("t.csv", csv.encode())},
        params={"target_column": "nope"},
    )
    assert resp.status_code == 400


def test_preview_empty_session(client, session_id):
    preview = client.get(f"/api/session/{session_id}/data/preview").json()
    assert preview == {"has_data": False}


def test_ai_route_requires_description(client, session_id):
    resp = client.post(f"/api/session/{session_id}/data/ai", json={"description": "  "})
    assert resp.status_code == 400


def test_ai_route_surface_llm_failure(client, session_id):
    client.put(f"/api/session/{session_id}/config", json={"data_source": "ai"})
    # Import path patched at consumer module; provider has no key → ValueError → 400
    resp = client.post(f"/api/session/{session_id}/data/ai", json={"description": "iris-like clustering set"})
    assert resp.status_code in (400, 502)
