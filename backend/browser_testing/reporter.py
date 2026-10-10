"""
AIForge Day 17 — Browser Test Report Generator
===============================================
Aggregates scenario results, accessibility findings, and visual regression results into a BrowserTestReport.
"""

from datetime import datetime
from typing import List

from backend.browser_testing.models import (
    BrowserTestReport, BrowserTestResult, AccessibilityFinding, VisualRegressionResult
)


class BrowserTestReporter:
    """
    Builds comprehensive BrowserTestReport objects.
    """

    def generate_report(
        self,
        project_id: str,
        results: List[BrowserTestResult],
        a11y_findings: List[AccessibilityFinding] = None,
        visual_results: List[VisualRegressionResult] = None
    ) -> BrowserTestReport:
        passed = sum(1 for r in results if r.status == "PASS")
        failed = sum(1 for r in results if r.status in ("FAIL", "ERROR"))
        skipped = sum(1 for r in results if r.status == "SKIPPED")
        total_dur = sum(r.duration_seconds for r in results)

        return BrowserTestReport(
            project_id=project_id,
            total_tests=len(results),
            passed_tests=passed,
            failed_tests=failed,
            skipped_tests=skipped,
            duration_seconds=round(total_dur, 2),
            browser_type="Chromium (Headless Docker Sandbox)",
            scenarios_results=results,
            accessibility_findings=a11y_findings or [],
            visual_regression_results=visual_results or [],
            created_at=datetime.now().isoformat()
        )


global_test_reporter = BrowserTestReporter()
