"""
AIForge V2 – Testing Report Validator Gate
==========================================
Validates structural completeness and test coverage thresholds of generated TestingReport packages.
"""

import logging
from typing import Tuple, List
from v2.agents.testing.models import TestingReport

_logger = logging.getLogger("aiforge.v2.testing.validator")


class TestingValidator:

    def validate_report(self, report: TestingReport) -> Tuple[bool, List[str]]:
        issues = []

        if not report.project_name:
            issues.append("Project name is missing.")

        if len(report.unit_tests) < 1:
            issues.append("No unit tests generated.")

        if len(report.api_tests) < 1:
            issues.append("No API tests generated.")

        if report.coverage.overall_coverage_pct < 80.0:
            issues.append(f"Overall test coverage ({report.coverage.overall_coverage_pct}%) below target threshold (80.0%).")

        if report.failed_count > 0:
            issues.append(f"Test suite execution contained {report.failed_count} failing tests.")

        is_valid = len(issues) == 0
        if is_valid:
            _logger.info(f"TestingValidator: Test suite for '{report.project_name}' PASSED validation gate with {report.passed_count} passed tests.")
        else:
            _logger.warning(f"TestingValidator: Validation issues detected: {issues}")

        return is_valid, issues


global_testing_validator = TestingValidator()
