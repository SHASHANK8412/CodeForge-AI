"""
AIForge V2 – Frontend Report Validator Gate
===========================================
Validates structural completeness and code quality of generated FrontendReport packages.
"""

import logging
from typing import Tuple, List
from v2.agents.frontend.models import FrontendReport

_logger = logging.getLogger("aiforge.v2.frontend.validator")


class FrontendValidator:

    def validate_report(self, report: FrontendReport) -> Tuple[bool, List[str]]:
        issues = []

        if not report.project_name:
            issues.append("Project name is missing.")

        if len(report.components) < 2:
            issues.append("Fewer than 2 UI components generated.")

        if len(report.pages) < 2:
            issues.append("Fewer than 2 pages generated.")

        if len(report.routes) < 2:
            issues.append("Fewer than 2 React Router routes configured.")

        if len(report.stores) < 1:
            issues.append("No Zustand state stores generated.")

        is_valid = len(issues) == 0
        if is_valid:
            _logger.info(f"FrontendValidator: Frontend package for '{report.project_name}' PASSED validation gate.")
        else:
            _logger.warning(f"FrontendValidator: Validation issues detected: {issues}")

        return is_valid, issues


global_frontend_validator = FrontendValidator()
