"""Cloud providers against mocked HTTP APIs (no real credentials or network)."""
import asyncio
import json

import httpx
import pytest

from backend.agents.devops_agent import DeploymentPlan, DeploymentReadinessScore, global_devops_agent
from backend.deployment.deployment_analyzer import DeploymentSpec
from backend.deployment.providers.neon_provider import NeonPostgresProvider
from backend.deployment.providers.render_provider import RenderProvider
from backend.deployment.providers.vercel_provider import VercelProvider

FILES = {
    "frontend/package.json": '{"name": "todo"}',
    "frontend/src/App.jsx": "export default () => null;",
    "backend/main.py": "app = None",
    "backend/requirements.txt": "fastapi\n",
}
DB_URL = "postgresql://alex:s3cr3t-pass@ep-x.neon.tech/neondb"


def run(coro):
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def _no_tokens(monkeypatch):
    for name in ("VERCEL_TOKEN", "VERCEL_TEAM_ID", "RENDER_API_KEY", "NEON_API_KEY"):
        monkeypatch.delenv(name, raising=False)


@pytest.mark.parametrize("provider,token_env", [
    (VercelProvider(), "VERCEL_TOKEN"), (RenderProvider(), "RENDER_API_KEY"), (NeonPostgresProvider(), "NEON_API_KEY"),
])
def test_missing_token_is_not_configured(provider, token_env):
    result = run(provider.deploy("todo", {"files": FILES}))
    assert result["status"] == "NOT_CONFIGURED" and result["url"] is None and token_env in result["message"]


def test_vercel_uploads_frontend_and_waits_until_ready(monkeypatch):
    monkeypatch.setenv("VERCEL_TOKEN", "vt")
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer vt"
        if request.method == "POST":
            seen["payload"] = json.loads(request.content)
            return httpx.Response(200, json={"id": "dpl_1", "url": "todo-abc.vercel.app", "readyState": "BUILDING"})
        return httpx.Response(200, json={"id": "dpl_1", "url": "todo-abc.vercel.app", "readyState": "READY"})

    provider = VercelProvider(transport=httpx.MockTransport(handler), poll_interval=0)
    result = run(provider.deploy("todo", {"files": FILES, "backend_url": "https://todo-api.onrender.com"}))

    assert result["status"] == "LIVE" and result["url"] == "https://todo-abc.vercel.app"
    uploaded = {f["file"] for f in seen["payload"]["files"]}
    assert uploaded == {"package.json", "src/App.jsx"}, "only frontend/, with the prefix stripped"
    assert seen["payload"]["build"]["env"]["VITE_API_URL"] == "https://todo-api.onrender.com"


def test_vercel_build_error_is_reported_as_failed(monkeypatch):
    monkeypatch.setenv("VERCEL_TOKEN", "vt")
    transport = httpx.MockTransport(lambda r: httpx.Response(200, json={"id": "d", "url": "x.vercel.app", "readyState": "ERROR"}))
    result = run(VercelProvider(transport=transport, poll_interval=0).deploy("todo", {"files": FILES}))
    assert result["status"] == "FAILED" and result["url"] is None


def test_vercel_api_rejection_surfaces_the_error(monkeypatch):
    monkeypatch.setenv("VERCEL_TOKEN", "vt")
    transport = httpx.MockTransport(lambda r: httpx.Response(403, json={"error": {"message": "Not authorized"}}))
    result = run(VercelProvider(transport=transport).deploy("todo", {"files": FILES}))
    assert result["status"] == "FAILED" and "Not authorized" in result["message"]


def test_neon_returns_masked_url_and_internal_credential(monkeypatch):
    monkeypatch.setenv("NEON_API_KEY", "nk")
    transport = httpx.MockTransport(lambda r: httpx.Response(201, json={
        "project": {"id": "proj_1"}, "connection_uris": [{"connection_uri": DB_URL}]}))
    result = run(NeonPostgresProvider(transport=transport).deploy("todo", {}))
    assert result["status"] == "LIVE" and result["neon_project_id"] == "proj_1"
    assert "s3cr3t-pass" not in result["database_url_masked"]
    assert result["_database_url"] == DB_URL


def test_render_without_a_repo_requires_github_export_first(monkeypatch):
    monkeypatch.setenv("RENDER_API_KEY", "rk")
    monkeypatch.setattr(RenderProvider, "_repo_url", staticmethod(lambda pid, cfg: None))
    result = run(RenderProvider().deploy("todo", {"files": FILES}))
    assert result["status"] == "MANUAL_DEPLOY_REQUIRED"


def test_render_creates_service_from_repo_and_waits_until_live(monkeypatch):
    monkeypatch.setenv("RENDER_API_KEY", "rk")
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/owners"):
            return httpx.Response(200, json=[{"owner": {"id": "own_1"}}])
        if request.method == "POST":
            seen["payload"] = json.loads(request.content)
            return httpx.Response(201, json={"service": {"id": "srv_1", "serviceDetails": {"url": "https://todo.onrender.com"}}, "deployId": "dep_1"})
        return httpx.Response(200, json={"status": "live"})

    provider = RenderProvider(transport=httpx.MockTransport(handler), poll_interval=0)
    result = run(provider.deploy("todo", {"files": FILES, "repo_url": "https://github.com/me/todo", "env_vars": {"DATABASE_URL": DB_URL}}))

    assert result["status"] == "LIVE" and result["url"] == "https://todo.onrender.com"
    assert seen["payload"]["ownerId"] == "own_1" and seen["payload"]["rootDir"] == "backend"
    assert {"key": "DATABASE_URL", "value": DB_URL} in seen["payload"]["envVars"]


def test_orchestration_wires_urls_and_never_returns_the_db_credential(monkeypatch):
    calls = {}

    async def neon(project_id, config):
        return {"provider": "neon", "status": "LIVE", "url": None, "database_url_masked": "postgresql://alex:****@h/db", "_database_url": DB_URL}

    async def render(project_id, config):
        calls["render"] = config
        return {"provider": "render", "status": "LIVE", "url": "https://todo.onrender.com"}

    async def vercel(project_id, config):
        calls["vercel"] = config
        return {"provider": "vercel", "status": "LIVE", "url": "https://todo.vercel.app"}

    import backend.agents.devops_agent as devops
    monkeypatch.setattr(devops.global_neon_provider, "deploy", neon)
    monkeypatch.setattr(devops.global_render_provider, "deploy", render)
    monkeypatch.setattr(devops.global_vercel_provider, "deploy", vercel)

    plan = DeploymentPlan(project_id="todo", spec=DeploymentSpec(), providers=["Vercel", "Render", "Neon"],
                          readiness=DeploymentReadinessScore(score=100, is_ready=True, status="READY"))
    result = run(global_devops_agent.execute_approved_deployment("todo", plan, approved_by_user=True))

    assert calls["render"]["env_vars"] == {"DATABASE_URL": DB_URL}
    assert calls["vercel"]["backend_url"] == "https://todo.onrender.com"
    assert result["status"] == "LIVE" and result["frontend_url"] == "https://todo.vercel.app"
    assert "s3cr3t-pass" not in json.dumps(result)
