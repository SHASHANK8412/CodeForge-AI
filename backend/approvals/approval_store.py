"""
AIForge Approval Store & Audit Trail
=====================================
Provides persistent memory store for approval requests, user feedback items, clarification Q&A items, and immutable audit logs.
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.approvals.store")


class ApprovalStore:
    """
    Stores approval requests, feedback items, clarification questions, and audit entries.
    """

    def __init__(self) -> None:
        self.approvals: Dict[str, Dict[str, Any]] = {
            "appr_001": {
                "id": "appr_001",
                "title": "Deploy Backend API to Production",
                "reason": "All automated test suites passing with 100% success rate.",
                "risk": "Medium",
                "affected_files": ["backend/main.py", "Dockerfile"],
                "estimated_time": "4 min",
                "status": "Pending",
                "requested_by": "DevOps Agent",
                "timestamp": time.time() - 1800,
                "history": [
                    {"status": "Pending", "timestamp": time.time() - 1800, "note": "Approval request created"}
                ]
            }
        }
        self.feedback_items: List[Dict[str, Any]] = []
        self.clarifications: List[Dict[str, Any]] = []
        self.audit_log: List[Dict[str, Any]] = [
            {
                "id": "audit_appr_1",
                "timestamp": time.time() - 1800,
                "event": "Approval Requested",
                "title": "Deploy Backend API to Production",
                "status": "Pending",
                "actor": "DevOps Agent"
            }
        ]

    def add_approval_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        req_id = request_data.get("id") or f"appr_{int(time.time() * 1000)}"
        request_data["id"] = req_id
        request_data["status"] = request_data.get("status", "Pending")
        request_data["timestamp"] = request_data.get("timestamp", time.time())
        request_data["history"] = [
            {"status": "Pending", "timestamp": time.time(), "note": "Approval request created"}
        ]
        self.approvals[req_id] = request_data

        # Audit entry
        self.log_audit_event("Approval Requested", request_data["title"], "Pending", request_data.get("requested_by", "AI Agent"))
        return request_data

    def respond_approval(self, approval_id: str, decision: str, reviewer_note: str = "") -> Dict[str, Any]:

        if approval_id not in self.approvals:
            raise ValueError(f"Approval request '{approval_id}' not found.")

        appr = self.approvals[approval_id]
        old_status = appr["status"]

        if decision == "Approve":
            appr["status"] = "Approved"
        elif decision == "Reject":
            appr["status"] = "Rejected"
        else:
            appr["status"] = decision

        appr["history"].append({
            "status": appr["status"],
            "timestamp": time.time(),
            "note": reviewer_note or f"Updated status from {old_status} to {appr['status']}"
        })

        self.log_audit_event(f"Approval {appr['status']}", appr["title"], appr["status"], "Human Reviewer")
        _logger.info(f"ApprovalStore: Approval '{approval_id}' updated to '{appr['status']}'")
        return appr

    def get_all_approvals(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        results = list(self.approvals.values())
        if status:
            results = [a for a in results if a["status"].lower() == status.lower()]
        return results

    def add_feedback(self, feedback_text: str, project_name: str = "Project") -> Dict[str, Any]:
        entry = {
            "id": f"fb_{int(time.time() * 1000)}",
            "feedback_text": feedback_text,
            "project_name": project_name,
            "timestamp": time.time()
        }
        self.feedback_items.append(entry)
        self.log_audit_event("Human Feedback Submitted", feedback_text, "Logged", "User")
        return entry

    def get_feedback(self) -> List[Dict[str, Any]]:
        return list(self.feedback_items)

    def get_all_feedback(self) -> List[Dict[str, Any]]:
        return list(self.feedback_items)

    def add_clarification_item(self, prompt: str, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        item = {
            "id": f"clarif_{int(time.time() * 1000)}",
            "original_prompt": prompt,
            "questions": questions,
            "status": "Awaiting User Input",
            "timestamp": time.time()
        }
        self.clarifications.append(item)
        return item

    def answer_clarification(self, item_id: str, answers: Dict[str, str]) -> Dict[str, Any]:
        for c in self.clarifications:
            if c["id"] == item_id:
                c["answers"] = answers
                c["status"] = "Answered"
                c["answered_at"] = time.time()
                self.log_audit_event("Clarification Answered", c["original_prompt"], "Answered", "User")
                return c
        raise ValueError(f"Clarification item '{item_id}' not found.")

    def log_audit_event(self, event: str, title: str, status: str, actor: str) -> Dict[str, Any]:
        entry = {
            "id": f"audit_appr_{int(time.time() * 1000)}",
            "timestamp": time.time(),
            "event": event,
            "title": title,
            "status": status,
            "actor": actor
        }
        self.audit_log.append(entry)
        return entry

    def get_audit_trail(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.audit_log[-limit:]


global_approval_store = ApprovalStore()
