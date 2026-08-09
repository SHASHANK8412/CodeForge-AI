"""
AIForge Approval Manager
========================
Coordinates human-in-the-loop approval requests, workflow pausing & resumption, ambiguity clarifications, human feedback task conversions, and approval dashboards.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from backend.agents.human_review_agent import global_human_review_agent
from backend.approvals.approval_store import global_approval_store

_logger = logging.getLogger("aiforge.approvals.manager")


class ApprovalManager:
    """
    Manages human approvals, workflow checkpoints, human feedback, and clarification questions.
    """

    def create_approval_request(
        self,
        title: str,
        reason: str,
        affected_files: List[str],
        risk: Optional[str] = None,
        estimated_time: str = "3 min",
        requested_by: str = "AI Agent"
    ) -> Dict[str, Any]:
        if risk is None:
            eval_res = global_human_review_agent.evaluate_action_risk(title, affected_files, reason)
            risk = eval_res["risk"]

        req_data = {
            "title": title,
            "reason": reason,
            "risk": risk,
            "affected_files": affected_files,
            "estimated_time": estimated_time,
            "requested_by": requested_by,
            "workflow_state": "PAUSED"
        }
        return global_approval_store.add_approval_request(req_data)

    def respond_to_request(self, approval_id: str, decision: str, reviewer_note: str = "") -> Dict[str, Any]:
        """
        decision: 'Approve' or 'Reject'
        """
        appr = global_approval_store.respond_approval(approval_id, decision, reviewer_note)
        
        # Resume workflow if approved
        if appr["status"] == "Approved":
            appr["workflow_state"] = "RESUMED"
            _logger.info(f"ApprovalManager: Workflow RESUMED for approved request '{approval_id}'")
        elif appr["status"] == "Rejected":
            appr["workflow_state"] = "REVISED_BY_PLANNER"
            _logger.info(f"ApprovalManager: Request '{approval_id}' REJECTED. Resubmitting to Planner for revision.")

        return appr

    def submit_user_feedback(self, feedback_text: str, project_name: str = "Project") -> Dict[str, Any]:
        feedback_entry = global_approval_store.add_feedback(feedback_text, project_name)
        new_tasks = global_human_review_agent.convert_feedback_to_tasks(feedback_text, project_name)
        return {
            "feedback": feedback_entry,
            "created_tasks_count": len(new_tasks),
            "created_tasks": new_tasks
        }

    def check_ambiguity_and_clarify(self, prompt: str) -> Dict[str, Any]:
        clarif = global_human_review_agent.generate_clarification(prompt)
        item = global_approval_store.add_clarification_item(prompt, clarif["clarification_questions"])
        return item

    def get_approval_dashboard(self) -> Dict[str, Any]:
        all_approvals = global_approval_store.get_all_approvals()
        pending = [a for a in all_approvals if a["status"] == "Pending"]
        approved = [a for a in all_approvals if a["status"] == "Approved"]
        rejected = [a for a in all_approvals if a["status"] == "Rejected"]
        audit_trail = global_approval_store.get_audit_trail()

        return {
            "timestamp": time.time(),
            "summary": {
                "total_requests": len(all_approvals),
                "pending": len(pending),
                "approved": len(approved),
                "rejected": len(rejected)
            },
            "pending_requests": pending,
            "approved_changes": approved,
            "rejected_changes": rejected,
            "audit_trail": audit_trail,
            "feedback_count": len(global_approval_store.get_all_feedback())
        }


global_approval_manager = ApprovalManager()
