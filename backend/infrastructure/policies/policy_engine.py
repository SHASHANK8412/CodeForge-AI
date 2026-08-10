"""
AIForge Day 32 — Infrastructure Policy Engine
=============================================
Enforces organization infrastructure policies (Zero Public Database, Encryption Required, Approval Gates).
"""

import logging
from typing import Dict, Any, List

from backend.infrastructure.terraform.models import TerraformPlan, SecurityAuditResult

_logger = logging.getLogger("aiforge.infrastructure.policies")


class InfrastructurePolicyEngine:
    """
    Policy engine validating infrastructure plan and security compliance.
    """

    def evaluate(
        self,
        plan: TerraformPlan,
        security_audit: SecurityAuditResult,
        environment: str = "production",
        user_approved: bool = False
    ) -> Dict[str, Any]:
        blocks = []
        warnings = []

        # 1. Security Violations -> BLOCK
        if not security_audit.passed:
            for v in security_audit.violations:
                blocks.append(f"SECURITY POLICY BLOCK: {v}")

        # 2. Production Destructive Operation -> BLOCK without user approval
        if environment.lower() == "production" and plan.is_destructive and not user_approved:
            blocks.append(
                f"DESTRUCTIVE POLICY BLOCK: Production plan contains {len(plan.destructive_resources)} "
                f"destructive change(s) ({plan.destructive_resources}). Explicit user policy approval is required."
            )

        allowed = len(blocks) == 0
        _logger.info(f"[PolicyEngine] Evaluation result: Allowed={allowed}, Blocks={len(blocks)}, Warnings={len(warnings)}")
        return {
            "allowed": allowed,
            "blocks": blocks,
            "warnings": warnings
        }


global_policy_engine = InfrastructurePolicyEngine()
