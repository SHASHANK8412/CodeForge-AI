import os
import shutil
import pytest
import subprocess
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.generators.project_generator import GENERATED_PROJECTS_DIR
from backend.deployment.deployment_analyzer import global_deployment_analyzer
from backend.deployment.validator import global_deployment_validator
from backend.routes.deployment import scan_secrets

client = TestClient(app)


@pytest.fixture
def setup_test_project():
    """Sets up a mock generated project directory for DevOps and Git verification."""
    project_id = "test_devops_project"
    project_dir = GENERATED_PROJECTS_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    # Create dummy app files
    (project_dir / "backend").mkdir(exist_ok=True)
    (project_dir / "backend/main.py").write_text(
        "import os\n"
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n"
        "@app.get('/health')\n"
        "def health():\n"
        "    return {'status': 'healthy'}\n"
        "DATABASE_URL = os.getenv('DATABASE_URL')\n",
        encoding="utf-8"
    )
    (project_dir / "frontend").mkdir(exist_ok=True)
    (project_dir / "frontend/index.html").write_text("<h1>Frontend</h1>", encoding="utf-8")

    yield project_id

    # Cleanup project using cmd rmdir to avoid permission blocks on Windows Git files
    if project_dir.exists():
        import subprocess
        subprocess.run(f'rmdir /s /q "{project_dir}"', shell=True)


def test_devops_agent_stack_detection(setup_test_project):
    project_id = setup_test_project
    project_dir = GENERATED_PROJECTS_DIR / project_id

    files_manifest = {
        "backend/main.py": (project_dir / "backend/main.py").read_text(),
        "frontend/index.html": (project_dir / "frontend/index.html").read_text()
    }

    # Verify Stack detection & spec extraction
    spec = global_deployment_analyzer.analyze(project_dir, files_manifest)
    assert spec.project_name == project_id
    assert spec.health_check_endpoint == "/health"
    assert "DATABASE_URL" in spec.required_env_vars

    # Verify pre-deployment file check (readiness check)
    val = global_deployment_validator.validate_deployment_files(files_manifest)
    assert "readiness_score" in val
    assert val["readiness_score"] < 100.0  # missing Dockerfile/docker-compose initially


def test_secret_scanner_deployment_gate(setup_test_project):
    project_id = setup_test_project
    project_dir = GENERATED_PROJECTS_DIR / project_id

    # 1. Write file with potential high-entropy secret
    secret_file = project_dir / "backend/config.py"
    secret_file.write_text("AWS_SECRET_ACCESS_KEY = \"AKIAIOSFODNN7EXAMPLEKEYS\"", encoding="utf-8")

    # Verify secret scanner matches it
    files = {"backend/config.py": secret_file.read_text()}
    findings = scan_secrets(files)
    assert len(findings) == 1
    assert findings[0]["key"] == "AWS_SECRET_ACCESS_KEY"
    assert "••••" in findings[0]["value_masked"]
    assert "AKIAIOSF" not in findings[0]["value_masked"]  # Ensure secret is redacted

    # Verify GET deployment returns status DEPLOYMENT_BLOCKED
    res = client.get(f"/api/projects/{project_id}/deployment")
    assert res.status_code == 200
    assert res.json()["status"] == "DEPLOYMENT_BLOCKED"

    # Verify trying to start deployment returns HTTP 400
    res_start = client.post(f"/api/projects/{project_id}/deployment/start")
    assert res_start.status_code == 400
    assert "secrets detected" in res_start.json()["detail"].lower()


def test_deployment_state_machine_flow(setup_test_project, monkeypatch):
    project_id = setup_test_project
    project_dir = GENERATED_PROJECTS_DIR / project_id

    from backend.deployment.providers.local_docker_provider import global_local_docker_provider
    from backend.deployment.providers.base_provider import ProviderDeploymentResult

    # Mock local docker deployment to return immediate success
    def mock_deploy(*args, **kwargs):
        return ProviderDeploymentResult(
            success=True,
            provider_name="LocalProcessMock",
            status="RUNNING",
            frontend_url="http://localhost:3000",
            backend_url="http://localhost:8000",
            stdout="Mock deploy output",
            stderr=""
        )
    monkeypatch.setattr(global_local_docker_provider, "deploy", mock_deploy)

    # Verify GET returns READY
    res = client.get(f"/api/projects/{project_id}/deployment")
    assert res.status_code == 200
    assert res.json()["status"] == "READY"

    # Start deployment
    res_start = client.post(f"/api/projects/{project_id}/deployment/start")
    assert res_start.status_code == 200
    assert res_start.json()["status"] == "QUEUED"

    # Fetch status shortly after to observe workflow logs
    res_status = client.get(f"/api/projects/{project_id}/deployment")
    assert res_status.json()["status"] in ("QUEUED", "BUILDING", "DEPLOYING", "LIVE")
    assert len(res_status.json()["logs"]) > 0


def test_git_github_router_endpoints(setup_test_project, monkeypatch):
    project_id = setup_test_project
    project_dir = GENERATED_PROJECTS_DIR / project_id

    from backend.routes import github_routes
    original_run_git = github_routes._run_git_cmd

    # Intercept git push commands to avoid live remote repository push authentication blocks
    def mock_run_git(project_dir, cmd):
        if "git push" in cmd:
            return "Everything up-to-date"
        return original_run_git(project_dir, cmd)
    monkeypatch.setattr(github_routes, "_run_git_cmd", mock_run_git)

    # 1. Git Init
    res_init = client.post("/api/github/git-init", json={"project_id": project_id})
    assert res_init.status_code == 200
    assert res_init.json()["success"] is True
    assert (project_dir / ".git").exists()
    assert (project_dir / ".gitignore").exists()

    # 2. Git Status
    res_status = client.get(f"/api/github/git-status?project_id={project_id}")
    assert res_status.status_code == 200
    assert res_status.json()["success"] is True
    assert "on branch" in res_status.json()["stdout"].lower()

    # 3. Git Commit
    res_commit = client.post("/api/github/commit", json={"project_id": project_id, "message": "feat: init commit"})
    assert res_commit.status_code == 200
    assert res_commit.json()["success"] is True

    # 4. Git Branch creation
    res_branch = client.post("/api/github/branch", json={"project_id": project_id, "branch_name": "aiforge/test-feature"})
    assert res_branch.status_code == 200
    assert res_branch.json()["success"] is True

    # 5. Connect Remote
    res_conn = client.post("/api/github/connect", json={"project_id": project_id, "repo_url": "https://github.com/SHASHANK8412/test-repo"})
    assert res_conn.status_code == 200
    assert res_conn.json()["status"] == "CONNECTED"

    # 6. Push
    res_push = client.post("/api/github/push", json={"project_id": project_id, "remote_url": "https://github.com/SHASHANK8412/test-repo"})
    assert res_push.status_code == 200
    assert res_push.json()["success"] is True

    # 7. Pull Request creation
    res_pr = client.post("/api/github/pull-request", json={
        "project_id": project_id,
        "title": "Autonomous bugfix integration",
        "body": "Fixes connection latency",
        "head_branch": "aiforge/test-feature",
        "base_branch": "main"
    })
    assert res_pr.status_code == 200
    pr_data = res_pr.json()
    assert pr_data["success"] is True
    assert pr_data["pr_number"] == 42
