"""
AIForge Day 19 — Production Readiness Gate Orchestrator
=========================================================
Runs readiness checks, calculates scores, evaluates policies, and invokes CTO Review Agent.
"""

import secrets
import logging
from datetime import datetime
from typing import List, Optional

from backend.readiness.models import ReadinessReport, ReadinessStatus
from backend.readiness.checks import global_readiness_check_collector
from backend.readiness.scoring import global_scoring_engine
from backend.readiness.policy import global_policy_engine
from backend.readiness.evaluator import global_cto_review_agent

_logger = logging.getLogger("aiforge.readiness.gate")


class ReadinessGate:
    """
    Orchestrates the Production Readiness Gate evaluation.
    """

    def evaluate_project(
        self,
        project_id: str,
        generation_id: str = "aiforge-demo",
        version: int = 1,
        simulate_security_block: bool = False
    ) -> ReadinessReport:
        _logger.info(f"[ReadinessGate] Evaluating production readiness for '{project_id}' v{version}")

        checks = global_readiness_check_collector.collect_all_checks(project_id, simulate_security_block)
        score = global_scoring_engine.calculate_score(checks)
        status, blockers, warnings = global_policy_engine.evaluate_policy(checks)

        if status == ReadinessStatus.BLOCKED:
            score = min(score, 71.0)

        cto_review = global_cto_review_agent.evaluate_readiness(status, score, checks, blockers, warnings)

        rep_id = f"rep_readiness_{secrets.token_urlsafe(6)}"
        return ReadinessReport(
            report_id=rep_id,
            project_id=project_id,
            generation_id=generation_id,
            version=version,
            status=status,
            overall_score=score,
            checks=checks,
            blocking_issues=blockers,
            warnings=warnings,
            recommendations=cto_review.required_actions,
            cto_review=cto_review,
            approval_status="PENDING",
            created_at=datetime.now().isoformat()
        )


global_readiness_gate = ReadinessGate()
