"""
AIForge V2 – Architecture Report Validator Gate
===============================================
Validates structural completeness and quality of generated ArchitectureReport packages.
"""

import logging
from typing import Tuple, List
from v2.agents.architect.models import ArchitectureReport

_logger = logging.getLogger("aiforge.v2.architect.validator")


class ArchitectureValidator:

    def validate_report(self, report: ArchitectureReport) -> Tuple[bool, List[str]]:
        issues = []

        if not report.project_name or report.project_name == "Software Project":
            issues.append("Project name is generic or missing.")

        if len(report.components) < 2:
            issues.append("Fewer than 2 system components specified.")

        if len(report.apis) < 2:
            issues.append("Fewer than 2 REST API endpoints designed.")

        if len(report.database.tables) < 2:
            issues.append("Fewer than 2 database tables designed.")

        if not report.security.auth_type:
            issues.append("Security authentication strategy missing.")

        is_valid = len(issues) == 0
        if is_valid:
            _logger.info(f"ArchitectureValidator: Architecture package for '{report.project_name}' PASSED validation gate.")
        else:
            _logger.warning(f"ArchitectureValidator: Validation issues detected: {issues}")

        return is_valid, issues


global_architecture_validator = ArchitectureValidator()
