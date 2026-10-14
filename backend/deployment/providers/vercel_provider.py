"""
Vercel Deployment Provider
==========================
Deploys a generated project's frontend/ to Vercel through the REST API
(POST /v13/deployments with inline files), then polls until the build settles.
"""

import asyncio
import logging
import os
import time
from typing import Any, Dict, Optional

import httpx

from backend.deployment.providers.base_provider import BaseDeploymentProvider
from backend.deployment.providers.cloud import api_error, failed, load_project_files, not_configured, slugify, subtree

_logger = logging.getLogger("aiforge.deployment.providers.vercel")

VERCEL_API = "https://api.vercel.com"
_PENDING_STATES = {"QUEUED", "INITIALIZING", "BUILDING"}


class VercelProvider(BaseDeploymentProvider):
    name = "vercel"
    display_name = "Vercel"
    service_type = "frontend"

    def __init__(self, transport: Optional[httpx.AsyncBaseTransport] = None,
                 poll_interval: float = 5.0, poll_timeout: float = 300.0) -> None:
        self.transport = transport
        self.poll_interval = poll_interval
        self.poll_timeout = poll_timeout

    def is_applicable(self, spec_data: Dict[str, Any]) -> bool:
        fe = spec_data.get("frontend_tech", "").lower()
        return any(tech in fe for tech in ["react", "vite", "next", "vue", "svelte"])

    async def prepare_config(self, spec_data: Dict[str, Any]) -> Dict[str, str]:
        return {
            "vercel.json": '{\n  "version": 2,\n  "buildCommand": "npm run build",\n  "outputDirectory": "dist",\n  "framework": "vite"\n}'
        }

    async def deploy(self, project_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        token = os.environ.get("VERCEL_TOKEN")
        if not token:
            return not_configured(self.name, self.display_name, "VERCEL_TOKEN")

        files = subtree(load_project_files(project_id, config), "frontend")
        if "package.json" not in files:
            return failed(self.name, "No frontend package.json found to deploy.")

        payload: Dict[str, Any] = {
            "name": slugify(project_id),
            "target": "production",
            "files": [{"file": path, "data": body} for path, body in files.items()],
            "projectSettings": {"framework": "vite", "buildCommand": "npm run build", "outputDirectory": "dist"},
        }
        if config.get("backend_url"):
            payload["build"] = {"env": {"VITE_API_URL": config["backend_url"]}}
        params = {"teamId": os.environ["VERCEL_TEAM_ID"]} if os.environ.get("VERCEL_TEAM_ID") else {}

        _logger.info("VercelProvider: deploying %d frontend files for '%s'", len(files), project_id)
        async with httpx.AsyncClient(base_url=VERCEL_API, timeout=60.0, transport=self.transport,
                                     headers={"Authorization": f"Bearer {token}"}) as client:
            resp = await client.post("/v13/deployments", json=payload, params=params)
            if resp.status_code >= 400:
                return failed(self.name, f"Vercel rejected the deployment: {api_error(resp)}")
            deployment = resp.json()

            deadline = time.monotonic() + self.poll_timeout
            while deployment.get("readyState") in _PENDING_STATES and time.monotonic() < deadline:
                await asyncio.sleep(self.poll_interval)
                resp = await client.get(f"/v13/deployments/{deployment['id']}", params=params)
                if resp.status_code >= 400:
                    return failed(self.name, f"Could not read deployment status: {api_error(resp)}")
                deployment = resp.json()

        state = deployment.get("readyState")
        status = "LIVE" if state == "READY" else "FAILED" if state in ("ERROR", "CANCELED") else "BUILDING"
        url = f"https://{deployment['url']}" if deployment.get("url") else None
        return {
            "provider": self.name,
            "status": status,
            "url": url if status != "FAILED" else None,
            "deployment_id": deployment.get("id"),
            "ready_state": state,
            "message": None if status == "LIVE" else f"Vercel deployment state: {state}",
        }


global_vercel_provider = VercelProvider()
