"""
AIForge V2 – Planner Report Validator Gate
==========================================
Validates the structural completeness and quality of generated PlannerReport blueprints.
"""

import logging
from typing import Dict, Any, List, Tuple
from v2.agents.planner.models import PlannerReport

_logger = logging.getLogger("aiforge.v2.planner.validator")


class PlannerReportValidator:
    """
    Validation gate checking completeness of PlannerReport deliverables.
    """

    def validate_report(self, report: PlannerReport) -> Tuple[bool, List[str]]:
        issues = []

        if not report.project_name or report.project_name == "Software Project":
            issues.append("Project name is missing or generic.")

        if not report.business_analysis.business_goal:
            issues.append("Business goal is missing.")

        if len(report.functional_requirements) < 2:
            issues.append("Fewer than 2 functional requirements specified.")

        if len(report.user_stories) < 1:
            issues.append("No Agile user stories generated.")

        if len(report.sprint_plan) < 1:
            issues.append("Sprint roadmap plan is empty.")

        if len(report.risk_analysis) < 1:
            issues.append("No technical risks identified.")

        is_valid = len(issues) == 0
        if is_valid:
            _logger.info(f"PlannerReportValidator: Report for '{report.project_name}' PASSED validation gate.")
        else:
            _logger.warning(f"PlannerReportValidator: Report validation issues detected: {issues}")

        return is_valid, issues


global_planner_validator = PlannerReportValidator()
