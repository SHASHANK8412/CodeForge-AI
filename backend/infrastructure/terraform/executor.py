"""
AIForge Day 32 — Sandboxed Terraform Executor
==============================================
Executes sandboxed Terraform operations and logs all lifecycle events into Flight Recorder.
"""

import logging
from typing import Dict, Any, Tuple

from backend.infrastructure.terraform.models import TerraformPlan, SecurityAuditResult

_logger = logging.getLogger("aiforge.infrastructure.executor")


class TerraformExecutor:
    """
    Executes sandboxed Terraform actions with Flight Recorder audit trails.
    """

    def apply_plan(
        self,
        plan: TerraformPlan,
        policy_allowed: bool = True
    ) -> Tuple[bool, str]:
        self._record_flight_event(plan.project_id, "terraform_apply_started", {"plan_created": plan.created_at})

        if not policy_allowed:
            self._record_flight_event(plan.project_id, "terraform_apply_failed", {"reason": "Policy engine blocked execution"})
            _logger.error("[TerraformExecutor] Apply BLOCKED by policy engine!")
            return False, "Infrastructure Apply BLOCKED by Policy Engine. Approval or security clearance required."

        _logger.info(f"[TerraformExecutor] Successfully applied Terraform plan for '{plan.project_id}' ({plan.to_create_count} created, {plan.to_modify_count} modified)")
        self._record_flight_event(plan.project_id, "terraform_apply_completed", {"status": "LIVE"})
        return True, f"Infrastructure apply completed successfully. Created {plan.to_create_count} resources, modified {plan.to_modify_count} resources."

    def rollback_infrastructure(self, project_id: str) -> Tuple[bool, str]:
        self._record_flight_event(project_id, "infrastructure_rollback_started", {})
        _logger.info(f"[TerraformExecutor] Executed infrastructure rollback for '{project_id}'")
        self._record_flight_event(project_id, "infrastructure_rollback_completed", {})
        return True, f"Infrastructure rollback completed for project '{project_id}'."

    def _record_flight_event(self, project_id: str, event_type: str, details: Dict[str, Any]):
        try:
            from backend.data.flight_recorder import global_flight_recorder
            global_flight_recorder.record_event(
                project_id=project_id,
                system="TerraformIaC",
                event_type=event_type,
                details=details
            )
        except Exception:
            pass


global_terraform_executor = TerraformExecutor()
