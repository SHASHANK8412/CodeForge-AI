"""
AIForge Day 20 — Automatic Rollback Engine
===========================================
Rolls back failed deployments to the last known-good version when health checks or smoke tests fail.
"""

import logging
from typing import Optional

from backend.devops.models import DeploymentStatus, DeploymentState
from backend.devops.providers.factory import global_provider_factory

_logger = logging.getLogger("aiforge.devops.rollback")

AUTO_ROLLBACK_ENABLED = True
MAX_ROLLBACK_ATTEMPTS = 1


class RollbackEngine:
    """
    Manages automated version rollbacks upon deployment failure.
    """

    def execute_rollback(self, project_id: str, current_version: int) -> DeploymentStatus:
        target_version = max(1, current_version - 1)
        _logger.warning(f"[RollbackEngine] Executing rollback for '{project_id}' from v{current_version} to v{target_version}")

        provider = global_provider_factory.get_provider("Docker")
        rolled_status = provider.rollback(project_id, target_version)
        rolled_status.status = DeploymentState.ROLLED_BACK
        return rolled_status


global_rollback_engine = RollbackEngine()
