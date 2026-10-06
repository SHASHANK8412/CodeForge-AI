"""
Render Deployment Provider
==========================
Handles async backend web service deployments (FastAPI, Express, Django, Docker).
"""

import time
import logging
from typing import Dict, Any
from backend.deployment.providers.base_provider import BaseDeploymentProvider, undeployed_result

_logger = logging.getLogger("aiforge.deployment.providers.render")


class RenderProvider(BaseDeploymentProvider):
    name = "render"
    display_name = "Render"
    service_type = "backend"

    def is_applicable(self, spec_data: Dict[str, Any]) -> bool:
        be = spec_data.get("backend_tech", "").lower()
        return any(tech in be for tech in ["fastapi", "python", "express", "django", "node"])

    async def prepare_config(self, spec_data: Dict[str, Any]) -> Dict[str, str]:
        yaml_content = """services:
  - type: web
    name: aiforge-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    autoDeploy: true
"""
        return {"render.yaml": yaml_content}

    async def deploy(self, project_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        _logger.info(f"RenderProvider: deploy requested for '{project_id}'")
        return undeployed_result(
            self.name, self.display_name, "RENDER_API_KEY",
            "Push the project to GitHub and create a Render Blueprint from the generated render.yaml.",
        )


global_render_provider = RenderProvider()
