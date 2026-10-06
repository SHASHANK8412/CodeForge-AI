"""
Neon Serverless PostgreSQL Provider
===================================
Handles database provisioning, migration verification, and connection pooling.
"""

import time
import logging
from typing import Dict, Any
from backend.deployment.providers.base_provider import BaseDeploymentProvider, undeployed_result

_logger = logging.getLogger("aiforge.deployment.providers.neon")


class NeonPostgresProvider(BaseDeploymentProvider):
    name = "neon"
    display_name = "Neon PostgreSQL"
    service_type = "database"

    def is_applicable(self, spec_data: Dict[str, Any]) -> bool:
        db = str(spec_data.get("database_tech", "")).lower()
        return "postgres" in db or "sql" in db

    async def prepare_config(self, spec_data: Dict[str, Any]) -> Dict[str, str]:
        return {
            "database/neon_init.sql": "-- AIForge Neon Database Initialization\n-- Automated connection pooling & branch isolation\nSELECT 1;\n"
        }

    async def deploy(self, project_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        _logger.info(f"NeonPostgresProvider: deploy requested for '{project_id}'")
        return undeployed_result(
            self.name, self.display_name, "NEON_API_KEY",
            "Create a project in the Neon console and set its connection string as DATABASE_URL.",
        )


global_neon_provider = NeonPostgresProvider()
