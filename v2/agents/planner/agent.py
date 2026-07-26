"""
AIForge V2 – Planner Agent Class
=================================
Planner Agent V2 converting business requests into comprehensive Product Blueprints.
"""

import time
import logging
from typing import Dict, Any, Optional
from v2.agents.base_agent_v2 import BaseAgentV2
from v2.agents.protocol import AgentRole
from v2.agents.planner.prompts import PLANNER_V2_SYSTEM_PROMPT
from v2.agents.planner.models import PlannerReport
from v2.agents.planner.parser import global_planner_parser
from v2.agents.planner.validator import global_planner_validator
from v2.logs.logger import global_v2_logger

_logger = logging.getLogger("aiforge.v2.planner")


class PlannerAgentV2(BaseAgentV2):
    """
    Planner Agent V2: Senior Product Manager & Business Analyst of AIForge V2.
    """

    def __init__(self):
        super().__init__(
            role=AgentRole.PLANNER,
            system_prompt=PLANNER_V2_SYSTEM_PROMPT
        )

    def generate_blueprint(self, prompt: str, project_id: str = "proj_v2_default") -> PlannerReport:
        started_at = time.perf_counter()
        _logger.info(f"PlannerAgentV2: Generating intelligent product blueprint for prompt: '{prompt[:60]}...'")

        raw_output = self.run(prompt)
        elapsed_ms = (time.perf_counter() - started_at) * 1000

        report = global_planner_parser.parse_report(raw_output, project_id=project_id)
        is_valid, issues = global_planner_validator.validate_report(report)

        global_v2_logger.log_agent_action(
            agent_name="planner",
            input_text=prompt,
            output_text=f"Blueprint generated. FRs: {len(report.functional_requirements)}, Stories: {len(report.user_stories)}, Sprints: {len(report.sprint_plan)}",
            execution_time_ms=elapsed_ms,
            metadata={
                "requirements_count": len(report.functional_requirements),
                "stories_count": len(report.user_stories),
                "features_count": len(report.prioritized_features),
                "risks_count": len(report.risk_analysis),
                "sprints_count": len(report.sprint_plan),
                "is_valid": is_valid
            }
        )

        return report


global_planner_agent_v2 = PlannerAgentV2()
