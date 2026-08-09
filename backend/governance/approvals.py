"""
AIForge Approval Engine
=======================
Manages human approval checkpoints (Requirements, Architecture, Generated Code, Deployment, Production Release).
Requires explicit human review before critical engineering operations proceed.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from backend.workspace.notifications import global_notification_manager

_logger = logging.getLogger("aiforge.governance.approvals")


class ApprovalEngine:
    """
    Manages approval workflow checkpoints, request creation, evaluation, and resolution.
    """

    CHECKPOINTS = ["Requirements", "Architecture", "Generated Code", "Deployment", "Production Release"]
    DECISIONS = ["Approved", "Rejected", "Revision Required"]

    def __init__(self) -> None:
        self.approval_requests: Dict[str, Dict[str, Any]] = {
            "req_arch_hospital": {
                "request_id": "req_arch_hospital",
                "project_id": "proj_hospital",
                "project_name": "Hospital Management System",
                "checkpoint": "Architecture",
                "title": "Hospital Management Microservices Architecture Review",
                "description": "Review system design blueprint including FHIR compliance & database schema.",
                "requester": "Architect Agent",
                "reviewer": "Lead Architect (Human)",
                "status": "Approved",
                "comments": "Approved architecture design with mandatory TLS 1.3 encryption.",
                "requested_at": time.time() - 7200,
                "responded_at": time.time() - 3600
            },
            "req_deploy_hospital": {
                "request_id": "req_deploy_hospital",
                "project_id": "proj_hospital",
                "project_name": "Hospital Management System",
                "checkpoint": "Deployment",
                "title": "Staging Deployment Approval",
                "description": "Deploy build #104 to Staging Kubernetes Cluster.",
                "requester": "DevOps Agent",
                "reviewer": "Project Manager",
                "status": "Pending",
                "comments": None,
                "requested_at": time.time() - 1200,
                "responded_at": None
            }
        }

    def request_approval(
        self,
        project_id: str,
        project_name: str,
        checkpoint: str,
        title: str,
        description: str,
        requester: str = "AI Agent"
    ) -> Dict[str, Any]:
        if checkpoint not in self.CHECKPOINTS:
            raise ValueError(f"Invalid checkpoint '{checkpoint}'. Allowed: {self.CHECKPOINTS}")

        req_id = f"req_{int(time.time() * 1000)}"
        request_obj = {
            "request_id": req_id,
            "project_id": project_id,
            "project_name": project_name,
            "checkpoint": checkpoint,
            "title": title,
            "description": description,
            "requester": requester,
            "reviewer": None,
            "status": "Pending",
            "comments": None,
            "requested_at": time.time(),
            "responded_at": None
        }
        self.approval_requests[req_id] = request_obj

        # Send notification
        global_notification_manager.notify(
            event_type="human_approval_required",
            project_id=project_id,
            project_name=project_name,
            title=f"Approval Required: {checkpoint}",
            message=f"Human review requested for '{title}' at checkpoint '{checkpoint}'.",
            metadata={"request_id": req_id}
        )

        _logger.info(f"ApprovalEngine: Requested approval '{req_id}' for '{title}' at checkpoint '{checkpoint}'")
        return request_obj

    def respond_to_approval(
        self,
        request_id: str,
        decision: str,
        reviewer: str = "Human Reviewer",
        comments: str = ""
    ) -> Dict[str, Any]:
        if decision not in self.DECISIONS:
            raise ValueError(f"Invalid decision '{decision}'. Allowed: {self.DECISIONS}")
        if request_id not in self.approval_requests:
            raise ValueError(f"Approval request '{request_id}' not found.")

        req = self.approval_requests[request_id]
        req["status"] = decision
        req["reviewer"] = reviewer
        req["comments"] = comments
        req["responded_at"] = time.time()

        _logger.info(f"ApprovalEngine: Request '{request_id}' responded with '{decision}' by '{reviewer}'")
        return req

    def get_pending_approvals(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        reqs = list(self.approval_requests.values())
        if project_id:
            reqs = [r for r in reqs if r["project_id"] == project_id]
        return [r for r in reqs if r["status"] == "Pending"]

    def get_all_requests(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        reqs = list(self.approval_requests.values())
        if project_id:
            reqs = [r for r in reqs if r["project_id"] == project_id]
        return reqs

    def is_checkpoint_approved(self, project_id: str, checkpoint: str) -> bool:
        matches = [
            r for r in self.approval_requests.values()
            if r["project_id"] == project_id and r["checkpoint"] == checkpoint and r["status"] == "Approved"
        ]
        return len(matches) > 0


global_approval_engine = ApprovalEngine()
