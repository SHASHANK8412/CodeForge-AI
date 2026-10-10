"""
Render Deployment Provider
==========================
Creates a Render web service for a generated project's backend through the REST API.
Render builds from a Git repository, so the project must be exported to GitHub first
(the repo URL comes from the deploy config or the GitHub repo store).
"""

import asyncio
import logging
import os
import time
from typing import Any, Dict, Optional

import httpx

from backend.deployment.providers.base_provider import BaseDeploymentProvider
from backend.deployment.providers.cloud import api_error, failed, load_project_files, not_configured, slugify

_logger = logging.getLogger("aiforge.deployment.providers.render")

RENDER_API = "https://api.render.com/v1"
_PENDING_DEPLOY = {"created", "build_in_progress", "update_in_progress", "pre_deploy_in_progress"}


class RenderProvider(BaseDeploymentProvider):
    name = "render"
    display_name = "Render"
    service_type = "backend"

    def __init__(self, transport: Optional[httpx.AsyncBaseTransport] = None,
                 poll_interval: float = 10.0, poll_timeout: float = 600.0) -> None:
        self.transport = transport
        self.poll_interval = poll_interval
        self.poll_timeout = poll_timeout

    def is_applicable(self, spec_data: Dict[str, Any]) -> bool:
        be = spec_data.get("backend_tech", "").lower()
        return any(tech in be for tech in ["fastapi", "python", "express", "django", "node"])

    async def prepare_config(self, spec_data: Dict[str, Any]) -> Dict[str, str]:
        yaml_content = """services:
  - type: web
    name: aiforge-backend
    runtime: python
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    autoDeploy: true
"""
        return {"render.yaml": yaml_content}

    @staticmethod
    def _repo_url(project_id: str, config: Dict[str, Any]) -> Optional[str]:
        if config.get("repo_url"):
            return config["repo_url"]
        from backend.github.repo_store import global_github_repo_store
        meta = global_github_repo_store.get(project_id)
        return meta.repo_url if meta else None

    async def deploy(self, project_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        token = os.environ.get("RENDER_API_KEY")
        if not token:
            return not_configured(self.name, self.display_name, "RENDER_API_KEY")

        repo_url = self._repo_url(project_id, config)
        if not repo_url:
            return {
                "provider": self.name,
                "status": "MANUAL_DEPLOY_REQUIRED",
                "url": None,
                "message": "Render deploys from a Git repository: export the project to GitHub first.",
            }

        files = load_project_files(project_id, config)
        root_dir = "backend" if any(p.startswith("backend/") for p in files) else ""
        env_vars = [{"key": k, "value": v} for k, v in (config.get("env_vars") or {}).items()]
        payload: Dict[str, Any] = {
            "type": "web_service",
            "name": slugify(project_id),
            "repo": repo_url,
            "branch": config.get("branch", "main"),
            "autoDeploy": "yes",
            "envVars": env_vars,
            "serviceDetails": {
                "runtime": "python",
                "plan": config.get("plan", "free"),
                "envSpecificDetails": {
                    "buildCommand": "pip install -r requirements.txt",
                    "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
                },
            },
        }
        if root_dir:
            payload["rootDir"] = root_dir

        _logger.info("RenderProvider: creating web service for '%s' from %s", project_id, repo_url)
        async with httpx.AsyncClient(base_url=RENDER_API, timeout=60.0, transport=self.transport,
                                     headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}) as client:
            owners = await client.get("/owners", params={"limit": 1})
            if owners.status_code >= 400 or not owners.json():
                return failed(self.name, f"Could not look up the Render account: {api_error(owners)}")
            payload["ownerId"] = owners.json()[0]["owner"]["id"]

            resp = await client.post("/services", json=payload)
            if resp.status_code >= 400:
                return failed(self.name, f"Render rejected the service: {api_error(resp)}")
            created = resp.json()
            service = created.get("service") or {}
            url = (service.get("serviceDetails") or {}).get("url")
            deploy_id = created.get("deployId")

            state = "created"
            deadline = time.monotonic() + self.poll_timeout
            while deploy_id and state in _PENDING_DEPLOY and time.monotonic() < deadline:
                await asyncio.sleep(self.poll_interval)
                dep = await client.get(f"/services/{service.get('id')}/deploys/{deploy_id}")
                if dep.status_code >= 400:
                    return failed(self.name, f"Could not read deploy status: {api_error(dep)}")
                state = dep.json().get("status", state)

        status = "LIVE" if state == "live" else "DEPLOYING" if state in _PENDING_DEPLOY else "FAILED"
        return {
            "provider": self.name,
            "status": status,
            "url": url if status != "FAILED" else None,
            "service_id": service.get("id"),
            "deploy_state": state,
            "message": None if status == "LIVE" else f"Render deploy state: {state}",
        }


global_render_provider = RenderProvider()
