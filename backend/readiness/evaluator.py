"""
AIForge Day 19 — CTO Review Agent
=================================
Evaluates structured readiness checks and generates executive summary, major risks,
recommendations, and production deployment advice without exposing hidden reasoning traces.
"""

import logging
from typing import List

from backend.readiness.models import CTOReview, ReadinessCheck, ReadinessStatus

_logger = logging.getLogger("aiforge.readiness.evaluator")


class CTOReviewAgent:
    """
    Independent CTO Review Agent evaluating readiness evidence.
    """

    def evaluate_readiness(
        self,
        status: ReadinessStatus,
        overall_score: float,
        checks: List[ReadinessCheck],
        blocking_issues: List[str],
        warnings: List[str]
    ) -> CTOReview:
        _logger.info(f"[CTOReviewAgent] Generating CTO review for status '{status.value}' (Score: {overall_score})")

        if status == ReadinessStatus.BLOCKED:
            return CTOReview(
                recommendation=ReadinessStatus.BLOCKED,
                executive_summary="DEPLOYMENT BLOCKED. The project contains critical security vulnerabilities or hard blocking issues.",
                major_risks=blocking_issues,
                required_actions=[
                    "Resolve all critical security findings and secret leaks.",
                    "Re-run Security Scan and Production Readiness Gate before attempting deployment."
                ]
            )

        if status == ReadinessStatus.READY_WITH_WARNINGS:
            return CTOReview(
                recommendation=ReadinessStatus.READY_WITH_WARNINGS,
                executive_summary=f"READY WITH WARNINGS (Score: {overall_score}/100). All core security, testing, and architecture checks passed.",
                major_risks=warnings,
                required_actions=[
                    "Review non-blocking documentation and browser warning items before final production rollout."
                ]
            )

        return CTOReview(
            recommendation=ReadinessStatus.READY,
            executive_summary=f"READY FOR PRODUCTION DEPLOYMENT (Score: {overall_score}/100). All engineering pipeline checks passed with zero blockers.",
            major_risks=[],
            required_actions=[
                "Obtain human approval and execute deployment pipeline."
            ]
        )


global_cto_review_agent = CTOReviewAgent()
