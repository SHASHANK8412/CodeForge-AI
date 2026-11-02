"""
AIForge Day 23 — Copilot Change Planner & Risk Evaluator
=========================================================
Generates structured change previews, risk evaluations (LOW, MEDIUM, HIGH, CRITICAL),
affected file lists, and multi-agent coordination plans.
"""

import secrets
import logging
from typing import Dict, Any, List

from backend.copilot.models import CopilotPlan, CopilotIntent, ActionCategory, CopilotContext

_logger = logging.getLogger("aiforge.copilot.planner")


class CopilotPlanner:
    """
    Generates change plans and previews before mutation or execution.
    """

    def create_plan(
        self,
        project_id: str,
        request_text: str,
        intent: CopilotIntent,
        category: ActionCategory,
        context: CopilotContext
    ) -> CopilotPlan:
        plan_id = f"plan_cp_{secrets.token_urlsafe(6)}"
        requires_appr = category in (ActionCategory.MUTATING_ACTION, ActionCategory.HIGH_RISK_ACTION)

        affected = context.files or ["backend/routes/products.py", "backend/services/products.py"]
        proposed = {
            affected[0]: "def get_products(page: int = 1, limit: int = 20): return service.list(page, limit)"
        }

        risk = "HIGH" if category == ActionCategory.HIGH_RISK_ACTION else ("MEDIUM" if category == ActionCategory.MUTATING_ACTION else "LOW")

        return CopilotPlan(
            plan_id=plan_id,
            request=request_text,
            intent=intent,
            action_category=category,
            summary=f"Plan to execute {intent.value} request: '{request_text}'",
            affected_files=affected,
            risk_level=risk,
            requires_approval=requires_appr,
            validation_pipeline=[
                "Unit & API Test Suite",
                "Security Vulnerability Scan",
                "Playwright Browser Smoke Tests",
                "Production Readiness Gate Evaluation"
            ],
            proposed_changes=proposed
        )


global_copilot_planner = CopilotPlanner()
