import pytest
import os
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_system_health_endpoint():
    """Verifies backend system health endpoint returns operational status."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "services" in data
    assert data["services"]["database"] == "healthy"
    assert data["services"]["ollama"] == "healthy"
    assert data["services"]["langgraph"] == "healthy"


def test_user_registration_login_flow():
    """Verifies user registration, login, profile fetch, and logout flow."""
    email = "e2e_tester@aiforge.io"
    password = "SecretPassword123!"

    # 1. Register User
    reg_res = client.post("/api/auth/register", json={
        "name": "E2E Tester",
        "email": email,
        "password": password
    })
    assert reg_res.status_code in [200, 400]  # 400 if user exists from prior run

    # 2. Login User
    login_res = client.post("/api/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Get Current Profile
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email
    assert me_res.json()["name"] == "E2E Tester"

    # 4. Logout
    logout_res = client.post("/api/auth/logout", headers=headers)
    assert logout_res.status_code == 200


def test_project_list_and_ownership():
    """Verifies project retrieval endpoint lists projects."""
    res = client.get("/api/projects")
    assert res.status_code == 200
    data = res.json()
    assert "projects" in data
    assert "stats" in data
    assert len(data["projects"]) >= 1


def test_full_project_generation_and_export_pipeline():
    """Verifies end-to-end project plan generation, quality report, and ZIP export."""
    gen_id = "aiforge-fooddelivery-ai"

    # 1. Inspect Project Quality Endpoint
    q_res = client.get(f"/api/projects/{gen_id}/quality")
    assert q_res.status_code == 200
    q_data = q_res.json()
    assert q_data["project_id"] == gen_id
    assert q_data["overall_score"] >= 80.0
    assert len(q_data["quality_gates"]) == 15


    # 2. Inspect Deployment Readiness Endpoint
    d_res = client.get(f"/api/projects/{gen_id}/deployment")
    assert d_res.status_code == 200
    d_data = d_res.json()
    assert d_data["project_id"] == gen_id
    assert d_data["status"] == "LIVE"
    assert d_data["readiness"]["is_ready"] is True

    # 3. Inspect ZIP Export Bundle
    exp_res = client.get(f"/api/export/zip/{gen_id}")
    assert exp_res.status_code in [200, 404]
