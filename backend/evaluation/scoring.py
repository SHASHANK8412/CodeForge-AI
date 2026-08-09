"""
AIForge Project Score Calculator
================================
Calculates empirical 100-point evaluation score breakdown across 7 weighted categories:
- Requirement Coverage: 20 points
- Code Correctness: 20 points
- Tests: 20 points
- Security: 15 points
- Architecture: 10 points
- Code Quality: 10 points
- Documentation: 5 points
Total = 100 points.
"""

import logging
from typing import Dict, Any, Optional
from backend.evaluation.models import EvaluationScoreBreakdown

_logger = logging.getLogger("aiforge.evaluation.scoring")


class ProjectScoreCalculator:
    """
    Computes dynamic score breakdowns based on real empirical evaluation metrics.
    """

    def calculate_scores(
        self,
        fidelity_result: Optional[Dict[str, Any]] = None,
        test_summary: Optional[Dict[str, Any]] = None,
        security_report: Optional[Dict[str, Any]] = None,
        architecture_spec: Optional[Dict[str, Any]] = None,
        static_analysis_report: Optional[Dict[str, Any]] = None,
        has_documentation: bool = True,
        execution_exit_code: int = 0
    ) -> EvaluationScoreBreakdown:
        _logger.info("ProjectScoreCalculator: Computing empirical evaluation score breakdown...")

        # 1. Requirement Coverage (20 pts max)
        req_cov_pts = 20.0
        if fidelity_result:
            domain_matched = fidelity_result.get("domain_matched", True)
            feat_cov = float(fidelity_result.get("feature_coverage", 100.0))
            if not domain_matched:
                req_cov_pts = min(4.0, round(feat_cov * 0.04, 1))
            else:
                req_cov_pts = round((feat_cov / 100.0) * 20.0, 1)

        # 2. Code Correctness (20 pts max)
        correctness_pts = 20.0
        if execution_exit_code != 0:
            correctness_pts -= 8.0

        if test_summary:
            total = test_summary.get("total_tests", 0)
            passed = test_summary.get("tests_passed", 0)
            if total > 0:
                pass_ratio = passed / total
                correctness_pts = round(min(20.0, correctness_pts * pass_ratio), 1)

        # 3. Tests (20 pts max)
        test_pts = 20.0
        if test_summary:
            total = test_summary.get("total_tests", 0)
            passed = test_summary.get("tests_passed", 0)
            if total > 0:
                test_pts = round((passed / total) * 20.0, 1)
            elif not test_summary.get("success", False):
                test_pts = 0.0

        # 4. Security (15 pts max)
        sec_pts = 15.0
        if security_report:
            sec_score = float(security_report.get("score", 100.0))
            sec_pts = round((sec_score / 100.0) * 15.0, 1)

        # 5. Architecture (10 pts max)
        arch_pts = 10.0
        if architecture_spec:
            if not architecture_spec.get("routes") or not architecture_spec.get("models"):
                arch_pts = 6.0

        # 6. Code Quality (10 pts max)
        quality_pts = 10.0
        if static_analysis_report:
            bugs = static_analysis_report.get("bugs_count", 0)
            quality_pts = round(max(0.0, 10.0 - (bugs * 2.0)), 1)

        # 7. Documentation (5 pts max)
        doc_pts = 5.0 if has_documentation else 0.0

        # Overall Sum
        overall = round(
            req_cov_pts + correctness_pts + test_pts + sec_pts + arch_pts + quality_pts + doc_pts,
            1
        )
        overall = max(0.0, min(100.0, overall))

        return EvaluationScoreBreakdown(
            requirement_coverage=req_cov_pts,
            code_correctness=correctness_pts,
            tests=test_pts,
            security=sec_pts,
            architecture=arch_pts,
            code_quality=quality_pts,
            documentation=doc_pts,
            overall_score=overall
        )


global_project_score_calculator = ProjectScoreCalculator()
