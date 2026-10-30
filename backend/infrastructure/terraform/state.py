"""
AIForge Day 32 — Infrastructure State & Drift Analyzer
======================================================
Manages Terraform state files securely and detects infrastructure drift without automatic overwriting.
"""

import logging
from typing import Dict, Any, Optional

from backend.infrastructure.terraform.models import DriftResult

_logger = logging.getLogger("aiforge.infrastructure.state")


class DriftAnalyzer:
    """
    Detects discrepancies between expected HCL configuration and live infrastructure state.
    """

    def detect_drift(
        self,
        project_id: str = "aiforge-demo",
        simulate_drift: bool = False
    ) -> DriftResult:
        _logger.info(f"[DriftAnalyzer] Checking infrastructure drift for project '{project_id}'")

        if simulate_drift:
            return DriftResult(
                has_drift=True,
                resource_name="aws_ecs_task_definition.backend",
                expected="3 replicas",
                actual="5 replicas",
                potential_cause="[simulated scenario] Manual scaling action applied directly on cloud provider console.",
                simulated=True,
            )
        # No Terraform state or cloud account is read, so drift is unknown - never reported as "in sync".
        return DriftResult(has_drift=None, potential_cause="Drift was not checked: no Terraform state or cloud account is read.")


global_drift_analyzer = DriftAnalyzer()
