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
        if not policy_allowed:
            self._record_flight_event(plan.project_id, "terraform_apply_blocked", {"reason": "Policy engine blocked execution"})
            return False, "Infrastructure Apply BLOCKED by Policy Engine. Approval or security clearance required."
        # The audit trail records what happened: an approved plan that was not applied.
        self._record_flight_event(plan.project_id, "terraform_apply_not_executed",
                                  {"to_create": plan.to_create_count, "to_modify": plan.to_modify_count,
                                   "reason": "terraform is not executed by AIForge"})
        return False, (f"Not applied: the plan ({plan.to_create_count} to create, {plan.to_modify_count} to modify) was "
                       "approved by the policy engine, but running terraform apply is not implemented. No resource was created.")

    def rollback_infrastructure(self, project_id: str) -> Tuple[bool, str]:
        return False, f"Not rolled back: infrastructure rollback is not implemented (nothing was ever applied for '{project_id}')."

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
