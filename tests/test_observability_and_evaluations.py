import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_observability_dashboard_endpoint():
    """Verifies /api/admin/observability returns health, generation metrics, agent performance, timelines, and cache stats."""
    # Register & Login User
    email = "obs_tester@aiforge.io"
    password = "SecretPassword123!"

    client.post("/api/auth/register", json={"name": "Obs Tester", "email": email, "password": password})
    login_res = client.post("/api/auth/login", json={"email": email, "password": password})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/admin/observability", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "health" in data
    assert data["health"]["backend"] == "HEALTHY"
    assert "generation_metrics" in data
    assert data["generation_metrics"]["total_generations"] >= 1000
    assert "agent_performance" in data
    assert len(data["agent_performance"]) >= 5
    assert "agent_timeline" in data
    assert "model_usage" in data
    assert "error_analytics" in data


def test_evaluations_center_endpoint():
    """Verifies /api/admin/evaluations returns benchmark dataset, regression score deltas, and agent metrics."""
    login_res = client.post("/api/auth/login", json={"email": "obs_tester@aiforge.io", "password": "SecretPassword123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/admin/evaluations", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "dataset" in data
    assert len(data["dataset"]) == 10
    assert data["overall_score"] >= 90.0
    assert "regression" in data
    assert data["regression"]["regression_detected"] is False
    assert "agent_evaluations" in data


def test_human_feedback_submission_flow():
    """Verifies submitting human quality feedback and retrieving project feedback records."""
    login_res = client.post("/api/auth/login", json={"email": "obs_tester@aiforge.io", "password": "SecretPassword123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    project_id = "aiforge-fooddelivery-ai"

    # Submit Feedback
    fb_res = client.post("/api/feedback", json={
        "project_id": project_id,
        "helpful": True,
        "rating": 5,
        "tags": ["Code quality", "Architecture"],
        "comment": "Excellent multi-agent project generation!"
    }, headers=headers)
    assert fb_res.status_code == 200
    assert fb_res.json()["success"] is True

    # Retrieve Project Feedback
    get_res = client.get(f"/api/feedback/{project_id}")
    assert get_res.status_code == 200
    fb_list = get_res.json()["feedback"]
    assert len(fb_list) >= 1
    assert fb_list[-1]["project_id"] == project_id
    assert fb_list[-1]["rating"] == 5
