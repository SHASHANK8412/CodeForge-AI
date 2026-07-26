"""
AIForge V2 – Planner Service Pipeline
======================================
Service wrapper coordinating requirement extraction, feature breakdown, risk assessment, and report persistence.
"""

import logging
from typing import Dict, Any, Optional
from v2.agents.planner.agent import global_planner_agent_v2
from v2.agents.planner.models import PlannerReport

_logger = logging.getLogger("aiforge.v2.planner.service")


class PlannerService:
    """
    Coordinates the full Requirements Engineering pipeline.
    """

    def analyze_project(self, prompt: str, project_id: str = "proj_v2_default") -> PlannerReport:
        _logger.info(f"PlannerService: Analyzing project requirements for project_id='{project_id}'")
        report = global_planner_agent_v2.generate_blueprint(prompt, project_id=project_id)
        return report


global_planner_service = PlannerService()
