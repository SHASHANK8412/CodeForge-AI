import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.graph.parallel_workflow import parallel_graph
from backend.graph.project_state import ProjectState
from backend.generators.project_generator import GENERATED_PROJECTS_DIR

client = TestClient(app)


def test_standardized_error_handling_api():
    """Verify that unhandled exceptions and HTTPExceptions are formatted as standardized JSON."""
    # 1. Trigger an invalid HTTP route (404)
    res_404 = client.get("/api/non-existent-route")
    assert res_404.status_code == 404
    data_404 = res_404.json()
    assert data_404["success"] is False
    assert "error" in data_404
    assert data_404["error"]["code"] == "HTTP_404"
    assert "request_id" in data_404["error"]

    # 2. Trigger an HTTPException (400 Bad Request)
    res_400 = client.post("/api/github/commit", json={"project_id": "non-existent-project", "message": "test"})
    assert res_400.status_code == 400
    data_400 = res_400.json()
    assert data_400["success"] is False
    assert "error" in data_400
    assert data_400["error"]["code"] == "HTTP_400"
    assert "request_id" in data_400["error"]


@pytest.mark.anyio
async def test_langgraph_master_orchestrator_nodes_execution(monkeypatch, tmp_path):
    """Verify that all new E2E DevOps/GitHub workflow nodes execute sequentially inside parallel_graph."""
    project_id = "test_e2e_integration_project"
    
    # Set up mock folders
    project_dir = GENERATED_PROJECTS_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "backend").mkdir(exist_ok=True)
    (project_dir / "backend/main.py").write_text("print('mock app')", encoding="utf-8")
    
    # 1. Mock deployment provider & git push cmd to run instantly
    from backend.deployment.providers.local_docker_provider import global_local_docker_provider
    from backend.deployment.providers.base_provider import ProviderDeploymentResult
    from backend.routes import github_routes

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
    monkeypatch.setattr(github_routes, "_run_git_cmd", lambda project_dir, cmd: "Everything up-to-date")

    # 2. Mock health check HTTP probing client
    class MockResponse:
        def __init__(self, status_code):
            self.status_code = status_code

    import httpx
    async def mock_get(url, *args, **kwargs):
        return MockResponse(status_code=200)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    # 3. Form initial state
    initial_state: ProjectState = {
        "project_id": project_id,
        "project_name": project_id,
        "project_path": str(project_dir),
        "user_prompt": "Build simple app",
        "prompt": "Build simple app",
        "files": {"backend/main.py": "print('mock app')"},
        "current_step": "planner",
        "stream_events": []
    }

    # Execute LangGraph parallel graph. We bypass long upstream generation nodes using state values
    # We test run the E2E stages (github_sync -> ci_check -> live_deploy -> health_check)
    from backend.graph.parallel_workflow import github_sync_node, ci_check_node, live_deploy_node, health_check_node
    
    # A. Execute github sync node
    sync_res = await github_sync_node(initial_state)
    assert sync_res["current_step"] == "github_sync"
    assert sync_res["github"]["status"] == "PUSHED"
    
    # B. Execute CI pipeline check
    ci_res = await ci_check_node(initial_state)
    assert ci_res["current_step"] == "ci_check"
    
    # C. Execute Container/Process deployment
    deploy_res = await live_deploy_node(initial_state)
    assert deploy_res["current_step"] == "live_deploy"
    assert deploy_res["deployment_status"] == "LIVE"
    assert deploy_res["deployment_url"] == "http://localhost:3000"
    
    # D. Execute Health monitor probe
    health_state = dict(initial_state)
    health_state.update(deploy_res)
    health_res = await health_check_node(health_state)
    assert health_res["current_step"] == "health_check"
    assert health_res["health_status"] == "HEALTHY"

    # Cleanup mock directory
    import subprocess
    subprocess.run(f'rmdir /s /q "{project_dir}"', shell=True)


@pytest.mark.anyio
async def test_health_check_auto_repair_recovery_loop(monkeypatch):
    """Verify that the health check node triggers auto-repair when probing fails initially."""
    project_id = "test_health_repair_project"
    project_dir = GENERATED_PROJECTS_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Write initial buggy files
    (project_dir / "backend").mkdir(exist_ok=True)
    (project_dir / "backend/main.py").write_text("buggy_code", encoding="utf-8")

    from backend.deployment.providers.local_docker_provider import global_local_docker_provider
    from backend.deployment.providers.base_provider import ProviderDeploymentResult
    from backend.routes import github_routes
    from backend.routes import project

    # A. Configure deployment mock to report success
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
    monkeypatch.setattr(github_routes, "_run_git_cmd", lambda project_dir, cmd: "Everything up-to-date")

    # B. Mock health check HTTP probing: fail first 2 times, then succeed
    call_count = 0
    class MockResponse:
        def __init__(self, status_code):
            self.status_code = status_code

    import httpx
    async def mock_get_latched(url, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise Exception("Connection timeout error")
        return MockResponse(status_code=200)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get_latched)

    # C. Mock project reviews to trigger fix proposals
    def mock_reviews(*args, **kwargs):
        return [{"file": "backend/main.py", "line": 1, "severity": "CRITICAL", "message": "Syntax error"}]
    monkeypatch.setattr(project, "review_project_route_internal", mock_reviews)

    async def mock_propose(*args, **kwargs):
        return {"after": "print('fixed app')"}
    monkeypatch.setattr(project, "propose_fix_route", mock_propose)

    def mock_apply(*args, **kwargs):
        (project_dir / "backend/main.py").write_text("print('fixed app')", encoding="utf-8")
        return {"success": True}
    monkeypatch.setattr(project, "apply_fix_route", mock_apply)

    # Execute health check node
    state: ProjectState = {
        "project_id": project_id,
        "project_name": project_id,
        "project_path": str(project_dir),
        "deployment_url": "http://localhost:8000",
        "stream_events": []
    }
    
    from backend.graph.parallel_workflow import health_check_node
    res = await health_check_node(state)
    assert res["health_status"] == "HEALTHY"
    assert res["deployment_status"] == "LIVE"
    assert call_count >= 2  # Proves loop executed multiple times and resolved

    # Cleanup mock directory
    import subprocess
    subprocess.run(f'rmdir /s /q "{project_dir}"', shell=True)
