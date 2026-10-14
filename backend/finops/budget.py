"""
AIForge Day 33 — Budget Manager
================================
Manages project budgets and raises warnings/critical alerts.
Does NOT automatically shut down production resources.
"""
from __future__ import annotations

from backend.finops.models import BudgetStatusEnum, ProjectBudget


class BudgetManager:
    """Creates and evaluates project budgets."""

    def create(
        self,
        project_id: str,
        environment: str = "production",
        monthly_limit: float = 250.0,
        alert_threshold: float = 0.80,
        current_estimate: float = 0.0,
    ) -> ProjectBudget:
        percent_used = round(current_estimate / monthly_limit, 4) if monthly_limit else 0.0

        if percent_used >= 1.0:
            status = BudgetStatusEnum.CRITICAL
        elif percent_used >= alert_threshold:
            status = BudgetStatusEnum.WARNING
        else:
            status = BudgetStatusEnum.OK

        return ProjectBudget(
            project_id=project_id,
            environment=environment,
            monthly_limit=monthly_limit,
            current_estimate=current_estimate,
            alert_threshold=alert_threshold,
            status=status,
            percent_used=round(percent_used * 100, 1),
        )

    def check(self, budget: ProjectBudget) -> dict:
        return {
            "project_id": budget.project_id,
            "monthly_limit": budget.monthly_limit,
            "current_estimate": budget.current_estimate,
            "percent_used": budget.percent_used,
            "status": budget.status,
            "action": _action_for_status(budget.status),
        }


def _action_for_status(status: BudgetStatusEnum) -> str:
    return {
        BudgetStatusEnum.OK:       "Within budget. No action required.",
        BudgetStatusEnum.WARNING:  "WARNING: Approaching budget limit. Review infrastructure spend.",
        BudgetStatusEnum.CRITICAL: "CRITICAL: Budget exceeded. Approval required before adding new resources. Do NOT automatically shut down production.",
    }[status]
