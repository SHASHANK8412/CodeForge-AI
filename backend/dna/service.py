"""
AIForge Day 15 — Centralized DNAService
=======================================
Manages project graph isolation, caching, real-time generation updates, and error handling.
"""

import logging
from typing import Dict, Any, List, Optional

from backend.dna.models import EngineeringDNAGraph, ImpactAnalysisResult
from backend.dna.analyzer import global_dna_analyzer
from backend.dna.repository import global_graph_repository
from backend.dna.impact import global_impact_engine

_logger = logging.getLogger("aiforge.dna.service")


class DNAService:
    """
    Centralized service for Engineering DNA.
    """

    def get_or_build_graph(
        self,
        project_id: str,
        files_map: Optional[Dict[str, str]] = None
    ) -> Optional[EngineeringDNAGraph]:
        existing = global_graph_repository.get_latest_graph(project_id)
        if existing:
            return existing

        if not files_map:
            # Seed default demo files map if none provided
            files_map = {
                "backend/auth.py": "def login_user(username, password):\n    pass",
                "backend/services/payment_service.py": "class PaymentService:\n    def process_payment(self, amount):\n        pass",
                "backend/routes/orders.py": "from backend.services.payment_service import PaymentService\ndef create_order():\n    pass",
                "frontend/src/components/Checkout.jsx": "export default function Checkout() { return <div/>; }",
                "tests/test_auth.py": "def test_login_user(): pass",
                "tests/test_payment.py": "def test_process_payment(): pass"
            }

        try:
            return global_dna_analyzer.analyze_project(project_id, files_map)
        except Exception as err:
            _logger.error(f"[DNAService] Graph analysis failed for project '{project_id}': {err}")
            return None

    def analyze_impact(self, project_id: str, node_id: str, change_type: str = "modify") -> ImpactAnalysisResult:
        # Ensure graph exists
        self.get_or_build_graph(project_id)
        return global_impact_engine.analyze_change_impact(project_id, node_id, change_type)


global_dna_service = DNAService()
