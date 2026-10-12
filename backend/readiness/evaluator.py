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
                executive_summary="BLOCKED. " + "; ".join(blocking_issues[:3]),
                major_risks=blocking_issues,
                required_actions=[
                    "Resolve the blocking issues listed above.",
                    "Evaluate readiness again after the fixes."
                ]
            )

        evaluated = [c for c in checks if c.status.value != "NOT_AVAILABLE"]
        missing = [c.category for c in checks if c.status.value == "NOT_AVAILABLE"]
        if status == ReadinessStatus.INCOMPLETE:
            return CTOReview(
                recommendation=ReadinessStatus.INCOMPLETE,
                executive_summary=(f"INSUFFICIENT EVIDENCE. {len(evaluated)} of {len(checks)} checks have evidence; "
                                   f"missing: {', '.join(missing)}. Readiness cannot be judged without security and test results."),
                major_risks=warnings,
                required_actions=["Run a Security Guardian assessment and the project's tests (Autopilot), then evaluate again."])

        if status == ReadinessStatus.READY_WITH_WARNINGS:
            return CTOReview(
                recommendation=ReadinessStatus.READY_WITH_WARNINGS,
                executive_summary=(f"READY WITH WARNINGS (Score: {overall_score}/100 over the evaluated checks). No blocking issue "
                                   f"was found; {len(warnings)} warning(s)" + (f"; no evidence for: {', '.join(missing)}" if missing else "") + "."),
                major_risks=warnings,
                required_actions=[
                    "Review the warnings before deploying."
                ]
            )

        return CTOReview(
            recommendation=ReadinessStatus.READY,
            executive_summary=(f"READY (Score: {overall_score}/100). All {len(evaluated)} evaluated checks passed"
                               + (f"; no evidence for: {', '.join(missing)}" if missing else "") + "."),
            major_risks=[],
            required_actions=[
                "Obtain human approval before deploying."
            ]
        )


global_cto_review_agent = CTOReviewAgent()
