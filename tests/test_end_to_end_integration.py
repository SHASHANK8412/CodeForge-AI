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
    # Each service is actually checked (they used to be hardcoded "healthy").
    assert data["services"]["api"] == "up"
    assert data["services"]["database"] == "up"
    assert data["services"]["ollama"] in ("up", "down", "error")


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


@pytest.fixture
def project(tmp_path, monkeypatch):
    """A finished generation of the signed-in (local-dev) user, with its folder under a scratch generated_projects/."""
    import backend.generators.project_generator as project_generator
    import backend.routes.export as export
    import backend.routes.project_manager as project_manager
    from backend.auth.service import DEFAULT_USER_ID
    from backend.generation.store import global_generation_store

    root = (tmp_path / "generated_projects").resolve()
    folder = root / "Notes_App"
    (folder / "backend").mkdir(parents=True)
    (folder / "backend" / "main.py").write_text("from fastapi import FastAPI\n\napp = FastAPI()\n", encoding="utf-8")
    (folder / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
    monkeypatch.setattr(export, "GENERATED_ROOT", root)
    monkeypatch.setattr(project_generator, "GENERATED_PROJECTS_DIR", root)
    monkeypatch.setattr(project_manager, "GENERATED_PROJECTS_DIR", root)
    gen_id = global_generation_store.create("Notes_App", DEFAULT_USER_ID, "a notes app")
    global_generation_store.set_output(gen_id, str(folder), 2)
    global_generation_store.update_status(gen_id, "completed")
    return gen_id


def test_project_list_and_ownership(project):
    """The project list returns the user's own generations."""
    res = client.get("/api/projects")
    assert res.status_code == 200
    data = res.json()
    assert "projects" in data and "stats" in data
    assert [p["latest_generation_id"] for p in data["projects"]] == [project]


def test_full_project_generation_and_export_pipeline(project):
    """Quality report, deployment readiness and ZIP export of a finished project. Quality gates come only from
    recorded checks: nothing has verified this project, so no gate is reported as passed and there is no score."""
    q_res = client.get(f"/api/projects/{project}/quality")
    assert q_res.status_code == 200
    q_data = q_res.json()
    assert q_data["project_id"] == project
    assert q_data["quality_gates"], "the gates are listed"
    assert q_data["overall_score"] is None
    assert all(g["status"] == "NOT_EVALUATED" for g in q_data["quality_gates"] if "test" in g["name"].lower())

    d_res = client.get(f"/api/projects/{project}/deployment")
    assert d_res.status_code == 200
    d_data = d_res.json()
    assert d_data["project_id"] == project
    # Never deployed in this test, so it must not be reported as live.
    assert d_data["status"] in ("READY", "DEPLOYMENT_BLOCKED")
    assert isinstance(d_data["readiness"]["is_ready"], bool)

    exp_res = client.get(f"/api/export/zip/{project}")
    assert exp_res.status_code == 200 and exp_res.content[:2] == b"PK"


def test_an_unknown_project_is_not_found():
    assert client.get("/api/projects/no-such-project/quality").status_code == 404
