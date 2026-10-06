"""
Vercel Deployment Provider
==========================
Handles static SPA / SSR frontend deployments (React, Vite, Next.js).
"""

import time
import logging
from typing import Dict, Any, List
from backend.deployment.providers.base_provider import BaseDeploymentProvider, undeployed_result

_logger = logging.getLogger("aiforge.deployment.providers.vercel")


class VercelProvider(BaseDeploymentProvider):
    name = "vercel"
    display_name = "Vercel"
    service_type = "frontend"

    def is_applicable(self, spec_data: Dict[str, Any]) -> bool:
        fe = spec_data.get("frontend_tech", "").lower()
        return any(tech in fe for tech in ["react", "vite", "next", "vue", "svelte"])

    async def prepare_config(self, spec_data: Dict[str, Any]) -> Dict[str, str]:
        return {
            "vercel.json": '{\n  "version": 2,\n  "buildCommand": "npm run build",\n  "outputDirectory": "dist",\n  "framework": "vite"\n}'
        }

    async def deploy(self, project_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        _logger.info(f"VercelProvider: deploy requested for '{project_id}'")
        return undeployed_result(
            self.name, self.display_name, "VERCEL_TOKEN",
            "Deploy manually from the frontend/ directory with `npx vercel --prod` (uses the generated vercel.json).",
        )


global_vercel_provider = VercelProvider()
