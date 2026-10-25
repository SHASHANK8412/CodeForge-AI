"""
AIForge Day 20 — Environment Configuration & Secret Validator
==============================================================
Manages environment configurations (development, testing, staging, production),
generates safe .env.example files with placeholders, and validates missing production variables.
"""

import logging
from typing import Dict, Any, List, Tuple

_logger = logging.getLogger("aiforge.devops.environment")

REQUIRED_PRODUCTION_VARS = ["DATABASE_URL", "JWT_SECRET", "API_BASE_URL"]


class EnvironmentManager:
    """
    Manages environment configs and validates required variables.
    """

    def validate_production_environment(
        self,
        env_vars: Dict[str, str]
    ) -> Tuple[bool, List[str]]:
        missing: List[str] = []
        for req in REQUIRED_PRODUCTION_VARS:
            val = env_vars.get(req, "").strip()
            if not val or val.startswith("YOUR_") or val == "placeholder":
                missing.append(req)

        if missing:
            _logger.warning(f"[EnvironmentManager] Missing production config: {missing}")
            return False, missing

        return True, []

    def generate_env_example(self) -> str:
        return (
            "# AIForge Generated .env.example (PLACEHOLDERS ONLY)\n"
            "DATABASE_URL=postgresql://user:password@localhost:5432/aiforge_db\n"
            "JWT_SECRET=your_production_jwt_secret_here\n"
            "API_BASE_URL=http://localhost:8080\n"
            "PORT=8080\n"
            "ENVIRONMENT=production\n"
        )


global_environment_manager = EnvironmentManager()
