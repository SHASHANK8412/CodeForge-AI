"""
AIForge Evolution - Migration & Evolution Planner
=================================================
Generates step-by-step code migration plans, risk mitigation strategies, and architectural consistency checks.
"""

import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.evolution")


class EvolutionPlanner:
    """
    Creates structured migration plans for code evolution operations.
    """

    def create_migration_plan(self, impact_report: Dict[str, Any]) -> Dict[str, Any]:
        prompt = impact_report.get("proposed_change", "")
        risk = impact_report.get("risk_level", "Low")
        affected_count = impact_report.get("affected_files_count", 1)

        steps = [
            f"1. Backup current codebase state and initialize rollback checkpoint.",
            f"2. Apply schema migration changes (Database tables & models).",
            f"3. Refactor API route definitions & controllers ({impact_report.get('requires_api_update')}).",
            f"4. Update frontend client components and state context ({impact_report.get('requires_frontend_update')}).",
            f"5. Execute selective unit & integration testing suite on affected files ({affected_count} files).",
            f"6. Update documentation (README, OpenAPI, Mermaid Architecture Diagram)."
        ]

        redesign_required = risk == "Critical"
        if redesign_required:
            _logger.warning("EvolutionPlanner: High architectural risk detected! Flagging for Planner redesign review.")

        return {
            "proposed_change": prompt,
            "risk_level": risk,
            "steps": steps,
            "redesign_required": redesign_required,
            "estimated_duration_seconds": affected_count * 2.5
        }
