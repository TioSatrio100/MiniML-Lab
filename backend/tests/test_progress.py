"""
test_progress.py — stats math incl. lower-is-better (recommendation/RMSE).
"""
def _log(client, sid, entries):
    """Write into Session.tracker recorded in the in-memory store."""
    from backend.core import session as session_store

    session_obj = session_store.get_session(sid)
    for e in entries:
        session_obj.tracker.log_experiment(
            iteration=e["iteration"],
            code="# test",
            execution_time=0.1,
            success=e["success"],
            metrics=e.get("metrics"),
        )


def test_progress_empty(client, session_id):
    resp = client.get(f"/api/session/{session_id}/progress")
    assert resp.status_code == 200
    stats = resp.json()["stats"]
    assert stats["total"] == 0
    assert stats["best_score"] == 0
    assert stats["improvement"] == 0
    assert stats["metric"] == "accuracy"


def test_progress_higher_is_better(client, session_id):
    client.post(f"/api/session/{session_id}/data/synthetic", json={"task_type": "classification", "n_samples": 40, "n_features": 4})
    seed = _log(client, session_id, [
        {"iteration": 1, "metrics": {"accuracy": 0.7}, "success": True},
        {"iteration": 2, "metrics": {"accuracy": 0.9}, "success": True},
        {"iteration": 3, "success": False},
    ])
    body = client.get(f"/api/session/{session_id}/progress").json()
    stats = body["stats"]
    assert stats["total"] == 3
    assert stats["successful"] == 2
    assert stats["best_score"] == 0.9
    assert abs(stats["improvement"] - 0.2) < 1e-9


def test_progress_lower_is_better_rmse(client, session_id):
    """recommendation task: RMSE lower-is-better → best = min, improvement = first - best."""
    client.put(f"/api/session/{session_id}/config", json={"task_type": "recommendation", "data_source": "csv"})
    client.post(f"/api/session/{session_id}/data/csv", files={"file": ("d.csv", b"user,item,rating\n1,2,4.0\n3,4,2.0\n")})
    _log(client, session_id, [
        {"iteration": 1, "metrics": {"rmse": 0.9}, "success": True},
        {"iteration": 2, "metrics": {"rmse": 0.4}, "success": True},
        {"iteration": 3, "metrics": {"rmse": 0.6}, "success": True},
    ])
    stats = client.get(f"/api/session/{session_id}/progress").json()["stats"]
    assert stats["metric"] == "rmse"
    assert stats["best_score"] == 0.4
    assert abs(stats["improvement"] - 0.5) < 1e-9


def _log(client, sid, entries):
    """Write into Session.tracker recorded in the in-memory store."""
    from backend.core import session as session_store

    session_obj = session_store.get_session(sid)
    for e in entries:
        session_obj.tracker.log_experiment(
            iteration=e["iteration"],
            code="# test",
            execution_time=0.1,
            success=e["success"],
            metrics=e.get("metrics"),
        )
