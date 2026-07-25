"""
AIForge V2 – Reviewer Report Validator Gate
===========================================
Validates structural completeness and quality assurance thresholds of generated ReviewReport packages.
"""

import logging
from typing import Tuple, List
from v2.agents.reviewer.models import ReviewReport

_logger = logging.getLogger("aiforge.v2.reviewer.validator")


class ReviewerValidator:

    def validate_report(self, report: ReviewReport) -> Tuple[bool, List[str]]:
        issues = []

        if not report.project_name:
            issues.append("Project name is missing.")

        if len(report.category_scores) < 4:
            issues.append("Fewer than 4 review categories scored.")

        if report.overall_score < 70.0:
            issues.append(f"Overall quality score ({report.overall_score}) is below approval threshold (70.0).")

        is_valid = len(issues) == 0
        if is_valid:
            _logger.info(f"ReviewerValidator: Code review for '{report.project_name}' PASSED validation gate with score {report.overall_score}%.")
        else:
            _logger.warning(f"ReviewerValidator: Validation issues detected: {issues}")

        return is_valid, issues


global_reviewer_validator = ReviewerValidator()
