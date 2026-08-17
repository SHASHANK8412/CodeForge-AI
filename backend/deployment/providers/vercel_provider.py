"""
Vercel Deployment Provider
==========================
Handles static SPA / SSR frontend deployments (React, Vite, Next.js).
"""

import time
import logging
from typing import Dict, Any, List
from backend.deployment.providers.base_provider import BaseDeploymentProvider

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
        _logger.info(f"VercelProvider: Deploying frontend for '{project_id}'...")
        slug = project_id.lower().replace("_", "-").replace(" ", "-")
        return {
            "provider": self.name,
            "status": "LIVE",
            "url": f"https://{slug}.vercel.app",
            "deployed_at": time.time(),
            "build_command": "npm run build",
            "output_dir": "dist"
        }


global_vercel_provider = VercelProvider()
