"""
FastAPI Routes for Day 28 Human-in-the-Loop & Enterprise Governance
====================================================================
Exposes REST APIs for human approvals, role-based access control (RBAC), audit logging, change history, review comments, and governance dashboards.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from backend.governance.approvals import global_approval_engine
from backend.governance.roles import global_rbac_manager
from backend.governance.audit import global_audit_logger
from backend.governance.history import global_change_history
from backend.governance.comments import global_review_comments
from backend.governance.reviewers import global_reviewer_manager
from backend.governance.reports import global_governance_reports

router = APIRouter(tags=["Enterprise Governance & Human-in-the-Loop"])


class ApprovalRequestInput(BaseModel):
    project_id: str
    project_name: str
    checkpoint: str
    title: str
    description: str
    requester: Optional[str] = "AI Agent"


class ApprovalResponseInput(BaseModel):
    request_id: str
    decision: str  # Approved, Rejected, Revision Required
    reviewer: Optional[str] = "Human Reviewer"
    comments: Optional[str] = ""


class AddCommentInput(BaseModel):
    project_id: str
    author: str
    author_role: str
    text: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    comment_type: Optional[str] = "General Feedback"


class RollbackInput(BaseModel):
    project_id: str
    version_id: str


class AssignRoleInput(BaseModel):
    user_id: str
    role: str


@router.post("/approval/request")
@router.post("/api/v1/approval/request")
async def create_approval_request(req: ApprovalRequestInput) -> Dict[str, Any]:
    """Triggers a human-in-the-loop approval checkpoint request (Requirements, Architecture, Generated Code, Deployment, Production Release)."""
    try:
        approval_req = global_approval_engine.request_approval(
            project_id=req.project_id,
            project_name=req.project_name,
            checkpoint=req.checkpoint,
            title=req.title,
            description=req.description,
            requester=req.requester
        )
        
        # Log to audit trail
        global_audit_logger.log_event(
            user_or_agent=req.requester,
            role="AI Agent",
            action=f"Requested Approval for Checkpoint '{req.checkpoint}'",
            target_entity=req.title,
            project_id=req.project_id,
            decision="Pending"
        )
        return {"status": "success", "approval_request": approval_req}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/approval/respond")
@router.post("/api/v1/approval/respond")
async def respond_approval_request(req: ApprovalResponseInput) -> Dict[str, Any]:
    """Responds to a human-in-the-loop approval request with Approved, Rejected, or Revision Required."""
    try:
        res = global_approval_engine.respond_to_approval(
            request_id=req.request_id,
            decision=req.decision,
            reviewer=req.reviewer,
            comments=req.comments
        )
        
        # Audit log entry
        global_audit_logger.log_event(
            user_or_agent=f"Reviewer ({req.reviewer})",
            role="Reviewer",
            action=f"{req.decision} Checkpoint '{res['checkpoint']}'",
            target_entity=res["title"],
            project_id=res["project_id"],
            decision=req.decision
        )
        return {"status": "success", "approval_result": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/approval/pending")
async def get_pending_approvals(project_id: Optional[str] = None) -> Dict[str, Any]:
    """Retrieves all pending human approval requests."""
    pending = global_approval_engine.get_pending_approvals(project_id=project_id)
    return {"status": "success", "pending_approvals": pending}


@router.get("/audit/logs")
@router.get("/api/v1/audit/logs")
async def get_audit_logs(
    project_id: Optional[str] = None,
    q: Optional[str] = Query(None, description="Search query string"),
    limit: int = 50
) -> Dict[str, Any]:
    """Retrieves immutable audit logs tracking actions by users and AI agents."""
    logs = global_audit_logger.get_logs(project_id=project_id, query=q, limit=limit)
    return {"status": "success", "total_logs": len(logs), "logs": logs}


@router.get("/project/history")
@router.get("/api/v1/project/history")
async def get_project_change_history(project_id: str = Query(..., description="Project ID")) -> Dict[str, Any]:
    """Retrieves code version history, AI diff summaries, and file change logs."""
    history = global_change_history.get_project_history(project_id=project_id)
    return {"status": "success", "project_id": project_id, "version_history": history}


@router.post("/project/rollback")
async def rollback_project_version(req: RollbackInput) -> Dict[str, Any]:
    """Rolls back project state to a specified previous version."""
    try:
        res = global_change_history.rollback_to_version(req.project_id, req.version_id)
        global_audit_logger.log_event(
            user_or_agent="Human Administrator",
            role="Administrator",
            action=f"Rolled back project to version '{req.version_id}'",
            target_entity=req.project_id,
            project_id=req.project_id,
            decision="Approved"
        )
        return {"status": "success", "rollback_result": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/comments/add")
@router.post("/api/v1/comments/add")
async def add_review_comment(req: AddCommentInput) -> Dict[str, Any]:
    """Adds inline code comment or task feedback discussion thread."""
    try:
        comment = global_review_comments.add_comment(
            project_id=req.project_id,
            author=req.author,
            author_role=req.author_role,
            text=req.text,
            file_path=req.file_path,
            line_number=req.line_number,
            comment_type=req.comment_type
        )
        return {"status": "success", "comment": comment}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/comments/list")
async def list_review_comments(project_id: Optional[str] = None, file_path: Optional[str] = None) -> Dict[str, Any]:
    """Lists review comments filtered by project or file path."""
    comments = global_review_comments.get_comments(project_id=project_id, file_path=file_path)
    return {"status": "success", "comments": comments}


@router.get("/governance/dashboard")
@router.get("/api/v1/governance/dashboard")
async def get_governance_dashboard() -> Dict[str, Any]:
    """Retrieves enterprise governance dashboard metrics, approval stats, compliance score, and audit timeline."""
    dash = global_governance_reports.get_governance_dashboard()
    return {"status": "success", "governance_dashboard": dash}


@router.get("/roles/list")
async def list_rbac_roles() -> Dict[str, Any]:
    """Lists RBAC roles and permissions matrix."""
    roles = global_rbac_manager.get_all_roles()
    return {"status": "success", "roles": roles}


@router.post("/roles/assign")
async def assign_user_role(req: AssignRoleInput) -> Dict[str, Any]:
    """Assigns user role in the RBAC matrix."""
    try:
        res = global_rbac_manager.assign_user_role(req.user_id, req.role)
        return {"status": "success", "role_assignment": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reviewers/list")
async def list_reviewers() -> Dict[str, Any]:
    """Lists active reviewers and review capacity."""
    reviewers = global_reviewer_manager.get_all_reviewers()
    return {"status": "success", "reviewers": reviewers}
