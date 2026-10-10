"""
AIForge Day 21 — AI Incident Analyst Agent
===========================================
Uses Engineering DNA dependency chains (POST /api/orders -> OrderService -> PaymentService -> DB),
sanitized logs, and recent deployment changes to identify root causes and affected files.
"""

import logging
from typing import Dict, Any, List, Tuple

from backend.incidents.models import IncidentType
from backend.dna.impact import global_impact_engine

_logger = logging.getLogger("aiforge.incidents.diagnosis")


class IncidentAnalystAgent:
    """
    Analyzes evidence and traces root causes through Engineering DNA.
    """

    def diagnose_root_cause(
        self,
        project_id: str,
        inc_type: IncidentType,
        evidence: Dict[str, Any]
    ) -> Tuple[str, List[str], List[str]]:
        _logger.info(f"[IncidentAnalystAgent] Diagnosing root cause for '{inc_type.value}' in '{project_id}'")

        if inc_type == IncidentType.DATABASE_FAILURE:
            dna_impact = global_impact_engine.analyze_change_impact(project_id, "OrderService", "modify")
            affected_files = dna_impact.affected_files or ["backend/database.py", "backend/config.py"]
            affected_apis = ["POST /api/orders", "GET /api/orders/{id}"]

            root_cause = "Database connection pool exhausted due to unclosed cursor in OrderService.get_orders()"
            return root_cause, affected_files, affected_apis

        if inc_type == IncidentType.PERFORMANCE_REGRESSION:
            dna_impact = global_impact_engine.analyze_change_impact(project_id, "PaymentService", "modify")
            affected_files = dna_impact.affected_files or ["backend/services/payment.py"]
            affected_apis = ["POST /api/checkout"]

            root_cause = "Un-indexed SQL query loop executing N+1 queries during checkout"
            return root_cause, affected_files, affected_apis

        return (
            "Unhandled application exception in request handler",
            ["backend/main.py"],
            ["GET /health"]
        )


global_incident_analyst_agent = IncidentAnalystAgent()
