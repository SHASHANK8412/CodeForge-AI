"""
AIForge V2 – Backend Report Validator Gate
==========================================
Validates structural completeness and code quality of generated BackendReport packages.
"""

import logging
from typing import Tuple, List
from v2.agents.backend.models import BackendReport

_logger = logging.getLogger("aiforge.v2.backend.validator")


class BackendValidator:

    def validate_report(self, report: BackendReport) -> Tuple[bool, List[str]]:
        issues = []

        if not report.project_name:
            issues.append("Project name is missing.")

        if len(report.apis) < 2:
            issues.append("Fewer than 2 REST API endpoints generated.")

        if len(report.services) < 1:
            issues.append("No service classes generated.")

        if len(report.repositories) < 1:
            issues.append("No repository classes generated.")

        if not report.auth.auth_type:
            issues.append("Authentication spec is missing.")

        if len(report.tests) < 1:
            issues.append("No unit tests generated.")

        is_valid = len(issues) == 0
        if is_valid:
            _logger.info(f"BackendValidator: Backend package for '{report.project_name}' PASSED validation gate.")
        else:
            _logger.warning(f"BackendValidator: Validation issues detected: {issues}")

        return is_valid, issues


global_backend_validator = BackendValidator()
