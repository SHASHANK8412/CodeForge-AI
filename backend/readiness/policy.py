"""
AIForge Day 19 — Hard Blocking Rules & Readiness Policy Engine
===============================================================
Enforces mandatory blocking conditions (Critical security findings, critical test failures, secret leaks, broken auth).
"""

import logging
from typing import List, Tuple

from backend.readiness.models import ReadinessCheck, CheckStatus, CheckSeverity, ReadinessStatus

_logger = logging.getLogger("aiforge.readiness.policy")


class HardBlockingPolicyEngine:
    """
    Determines overall ReadinessStatus (READY, READY_WITH_WARNINGS, BLOCKED, INCOMPLETE)
    and collects blocking issues vs warnings.
    """

    def evaluate_policy(self, checks: List[ReadinessCheck]) -> Tuple[ReadinessStatus, List[str], List[str]]:
        blocking_issues: List[str] = []
        warnings: List[str] = []

        for c in checks:
            if c.blocking or c.status == CheckStatus.FAIL or (c.severity == CheckSeverity.CRITICAL and c.status != CheckStatus.PASS):
                blocking_issues.append(f"[{c.category}] {c.name}: {c.evidence}")
            elif c.status == CheckStatus.WARN:
                warnings.append(f"[{c.category}] {c.name}: {c.evidence}")

        if blocking_issues:
            return ReadinessStatus.BLOCKED, blocking_issues, warnings
        elif warnings:
            return ReadinessStatus.READY_WITH_WARNINGS, [], warnings
        else:
            return ReadinessStatus.READY, [], []


global_policy_engine = HardBlockingPolicyEngine()
