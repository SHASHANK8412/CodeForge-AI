"""
FastAPI Routes for Day 31 Human-in-the-Loop AI Development
===========================================================
Exposes REST APIs for human approval requests, responses, workflow pausing/resumption, human feedback task conversion, ambiguity clarifications, and approval dashboards.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from backend.approvals.approval_manager import global_approval_manager
from backend.approvals.approval_store import global_approval_store

router = APIRouter(tags=["Human-in-the-Loop (HITL) AI Development"])


class CreateApprovalInput(BaseModel):
    title: str
    reason: str
    affected_files: List[str]
    risk: Optional[str] = None
    estimated_time: Optional[str] = "4 min"
    requested_by: Optional[str] = "AI Agent"


class RespondApprovalInput(BaseModel):
    approval_id: str
    decision: str  # Approve or Reject
    reviewer_note: Optional[str] = ""


class SubmitFeedbackInput(BaseModel):
    feedback_text: str
    project_name: Optional[str] = "Project"


class AskClarificationInput(BaseModel):
    prompt: str


class AnswerClarificationInput(BaseModel):
    item_id: str
    answers: Dict[str, str]


@router.get("/approvals")
@router.get("/api/v1/approvals")
async def list_approvals(status: Optional[str] = Query(None, description="Filter by status: Pending, Approved, Rejected")) -> Dict[str, Any]:
    """Retrieves all human approval requests and statuses."""
    approvals = global_approval_store.get_all_approvals(status=status)
    return {"status": "success", "total_approvals": len(approvals), "approvals": approvals}


@router.post("/approvals/create")
@router.post("/api/v1/approvals/create")
async def create_approval_request(req: CreateApprovalInput) -> Dict[str, Any]:
    """Creates a new human approval request before performing a high-risk operation, pausing the workflow."""
    try:
        appr = global_approval_manager.create_approval_request(
            title=req.title,
            reason=req.reason,
            affected_files=req.affected_files,
            risk=req.risk,
            estimated_time=req.estimated_time or "4 min",
            requested_by=req.requested_by or "AI Agent"
        )
        return {"status": "success", "approval_request": appr}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/approvals/respond")
@router.post("/api/v1/approvals/respond")
async def respond_to_approval_request(req: RespondApprovalInput) -> Dict[str, Any]:
    """Responds to an approval request with Approve (resumes workflow) or Reject (revises plan)."""
    try:
        res = global_approval_manager.respond_to_request(
            approval_id=req.approval_id,
            decision=req.decision,
            reviewer_note=req.reviewer_note or ""
        )
        return {"status": "success", "approval_result": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/feedback")
@router.get("/api/v1/feedback")
async def get_all_human_feedback() -> Dict[str, Any]:
    """Retrieves all submitted human feedback items."""
    feedback_items = global_approval_store.get_all_feedback()
    return {"status": "success", "total_feedback": len(feedback_items), "feedback": feedback_items}


@router.post("/feedback")
@router.post("/api/v1/feedback")
async def submit_human_feedback(req: SubmitFeedbackInput) -> Dict[str, Any]:
    """Submits human feedback and automatically converts it into actionable engineering tasks."""
    try:
        res = global_approval_manager.submit_user_feedback(req.feedback_text, req.project_name or "Project")
        return {"status": "success", "feedback_result": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/clarifications/ask")
@router.post("/api/v1/clarifications/ask")
async def ask_clarification_questions(req: AskClarificationInput) -> Dict[str, Any]:
    """Evaluates prompt ambiguity and generates clarification questions for the user."""
    item = global_approval_manager.check_ambiguity_and_clarify(req.prompt)
    return {"status": "success", "clarification_item": item}


@router.post("/clarifications/answer")
@router.post("/api/v1/clarifications/answer")
async def answer_clarification_questions(req: AnswerClarificationInput) -> Dict[str, Any]:
    """Records user answers to clarification questions."""
    try:
        ans = global_approval_store.answer_clarification(req.item_id, req.answers)
        return {"status": "success", "answered_clarification": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/approvals/dashboard")
@router.get("/api/v1/approvals/dashboard")
async def get_approval_dashboard() -> Dict[str, Any]:
    """Retrieves Approval Dashboard data: Pending/Approved/Rejected requests, Risk Levels, and Audit Trail."""
    dash = global_approval_manager.get_approval_dashboard()
    return {"status": "success", "approval_dashboard": dash}


# ---------------------------------------------------------------------------
# Human-in-the-Loop Workflow Approval Endpoints
# ---------------------------------------------------------------------------

class ApproveWorkflowInput(BaseModel):
    notes: Optional[str] = ""


class RejectWorkflowInput(BaseModel):
    feedback: str


from backend.generation.manager import global_generation_manager


@router.post("/api/projects/{project_id}/approve")
@router.post("/api/generations/{generation_id}/approve")
async def approve_workflow_stage(
    project_id: Optional[str] = None,
    generation_id: Optional[str] = None,
    payload: Optional[ApproveWorkflowInput] = None
) -> Dict[str, Any]:
    """
    Approves a paused workflow at an approval checkpoint (Architecture or Final Review)
    and resumes multi-agent execution from the checkpoint.
    """
    target_id = generation_id or project_id
    if not target_id:
        raise HTTPException(status_code=400, detail="Project ID or Generation ID is required.")

    notes = payload.notes if payload else ""
    try:
        res = await global_generation_manager.approve_generation(target_id, notes=notes)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume workflow: {str(e)}")


@router.post("/api/projects/{project_id}/reject")
@router.post("/api/generations/{generation_id}/reject")
async def reject_workflow_stage(
    payload: RejectWorkflowInput,
    project_id: Optional[str] = None,
    generation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Rejects a workflow stage with specific feedback, storing the feedback and
    resuming the workflow through the appropriate agent to revise the plan/code.
    """
    target_id = generation_id or project_id
    if not target_id:
        raise HTTPException(status_code=400, detail="Project ID or Generation ID is required.")

    if not payload.feedback or not payload.feedback.strip():
        raise HTTPException(status_code=400, detail="Rejection feedback cannot be empty.")

    try:
        res = await global_generation_manager.reject_generation(target_id, feedback=payload.feedback.strip())
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process rejection: {str(e)}")


@router.get("/api/projects/{project_id}/status")
@router.get("/api/generations/{generation_id}/status")
async def get_workflow_status(
    project_id: Optional[str] = None,
    generation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieves full real-time workflow status including checkpoint data, approval state,
    and active agents. Survives browser reloads and server restarts.
    """
    target_id = generation_id or project_id
    if not target_id:
        raise HTTPException(status_code=400, detail="Project ID or Generation ID is required.")

    try:
        status_data = global_generation_manager.get_status(target_id)
        return status_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve workflow status: {str(e)}")

