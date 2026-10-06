"""
Neon Serverless PostgreSQL Provider
===================================
Provisions a Neon Postgres project through the REST API (POST /api/v2/projects).
The full connection string is a credential: it is handed to the backend deploy
internally and only ever returned masked.
"""

import logging
import os
from typing import Any, Dict, Optional

import httpx

from backend.deployment.providers.base_provider import BaseDeploymentProvider
from backend.deployment.providers.cloud import api_error, failed, mask_database_url, not_configured, slugify

_logger = logging.getLogger("aiforge.deployment.providers.neon")

NEON_API = "https://console.neon.tech/api/v2"


class NeonPostgresProvider(BaseDeploymentProvider):
    name = "neon"
    display_name = "Neon PostgreSQL"
    service_type = "database"

    def __init__(self, transport: Optional[httpx.AsyncBaseTransport] = None) -> None:
        self.transport = transport

    def is_applicable(self, spec_data: Dict[str, Any]) -> bool:
        db = str(spec_data.get("database_tech", "")).lower()
        return "postgres" in db or "sql" in db

    async def prepare_config(self, spec_data: Dict[str, Any]) -> Dict[str, str]:
        return {
            "database/neon_init.sql": "-- AIForge Neon Database Initialization\nSELECT 1;\n"
        }

    async def deploy(self, project_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        token = os.environ.get("NEON_API_KEY")
        if not token:
            return not_configured(self.name, self.display_name, "NEON_API_KEY")

        _logger.info("NeonPostgresProvider: creating database project for '%s'", project_id)
        async with httpx.AsyncClient(base_url=NEON_API, timeout=60.0, transport=self.transport,
                                     headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}) as client:
            resp = await client.post("/projects", json={"project": {"name": slugify(project_id)}})
        if resp.status_code >= 400:
            return failed(self.name, f"Neon rejected the project: {api_error(resp)}")

        body = resp.json()
        uris = body.get("connection_uris") or []
        database_url = uris[0].get("connection_uri") if uris else None
        if not database_url:
            return failed(self.name, "Neon created the project but returned no connection string.")

        return {
            "provider": self.name,
            "status": "LIVE",
            "url": None,
            "neon_project_id": (body.get("project") or {}).get("id"),
            "database_url_masked": mask_database_url(database_url),
            # Internal only: DevOpsAgent forwards it to the backend and strips it from responses.
            "_database_url": database_url,
        }


global_neon_provider = NeonPostgresProvider()
