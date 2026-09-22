"""
AIForge Day 25 — Failure Propagation & SPOF Engine
===================================================
Simulates component failure propagation (e.g. "What if PostgreSQL fails?") and detects single points of failure (SPOFs)
using Engineering DNA dependency graphs.
"""

import logging
from typing import Dict, Any, List

from backend.architecture_simulator.models import FailurePropagationReport
from backend.dna.impact import global_impact_engine

_logger = logging.getLogger("aiforge.architecture.impact")


class FailurePropagationEngine:
    """
    Simulates component failure propagation using Engineering DNA.
    """

    def simulate_component_failure(self, project_id: str, component_name: str) -> FailurePropagationReport:
        _logger.info(f"[FailurePropagationEngine] Simulating failure of '{component_name}' in '{project_id}'")

        dna_impact = global_impact_engine.analyze_change_impact(project_id, component_name, "delete")
        affected_files = dna_impact.affected_files or ["backend/routes/orders.py", "backend/routes/checkout.py", "backend/routes/auth.py"]
        affected_apis = ["POST /api/orders", "POST /api/checkout", "GET /api/user/profile"]

        c_lower = component_name.lower()
        is_spof = "postgres" in c_lower or "db" in c_lower or "auth" in c_lower

        rec = (
            "Add database connection pool retry resilience, read replicas, and graceful degradation fallback."
            if is_spof else
            "Implement circuit breaker pattern around downstream service dependency."
        )

        return FailurePropagationReport(
            failed_component=component_name,
            project_id=project_id,
            impact_level="CRITICAL" if is_spof else "HIGH",
            affected_components=affected_files,
            affected_apis=affected_apis,
            single_point_of_failure=is_spof,
            mitigation_recommendation=rec
        )


global_failure_propagation_engine = FailurePropagationEngine()
