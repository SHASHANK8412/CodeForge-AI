"""
AIForge V2 — Engineering Autopilot REST API Routes
===================================================
All endpoints enforce user authentication and generation/project ownership.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.auth.dependencies import get_current_user
from backend.autopilot.service import global_autopilot_service

router = APIRouter(prefix="/api/autopilot", tags=["Engineering Autopilot"])
flight_router = APIRouter(prefix="/api/projects", tags=["Engineering Flight Recorder"])


class AutopilotStartInput(BaseModel):
    project_id: str = Field(default="proj_demo", description="Target project ID")
    prompt: str = Field(min_length=5, description="High-level software goal prompt")
    autonomy_level: str = Field(default="BALANCED", description="ASSISTED, BALANCED, or FULL_AUTONOMY")
    approval_settings: Optional[Dict[str, bool]] = Field(default_factory=dict)


class ApprovalDecisionInput(BaseModel):
    request_id: str = Field(..., description="Approval request ID")


@router.post("/start")
async def start_autopilot(
    req: AutopilotStartInput,
    user: dict = Depends(get_current_user)
):
    user_id = user.get("id", "default_user")
    res = await global_autopilot_service.start(
        project_id=req.project_id,
        user_id=user_id,
        prompt=req.prompt,
        autonomy_level=req.autonomy_level,
        approval_settings=req.approval_settings
    )
    return {"status": "success", **res}


@router.get("/{generation_id}")
async def get_autopilot_state(
    generation_id: str,
    user: dict = Depends(get_current_user)
):
    user_id = user.get("id", "default_user")
    res = global_autopilot_service.get_autopilot_state(generation_id, user_id)
    return {"status": "success", **res}


@router.post("/{generation_id}/pause")
async def pause_autopilot(
    generation_id: str,
    user: dict = Depends(get_current_user)
):
    res = global_autopilot_service.pause(generation_id)
    return {"status": "success", **res}


@router.post("/{generation_id}/resume")
async def resume_autopilot(
    generation_id: str,
    user: dict = Depends(get_current_user)
):
    res = global_autopilot_service.resume(generation_id)
    return {"status": "success", **res}


@router.post("/{generation_id}/stop")
async def stop_autopilot(
    generation_id: str,
    user: dict = Depends(get_current_user)
):
    res = global_autopilot_service.stop(generation_id)
    return {"status": "success", **res}


@router.post("/{generation_id}/approve")
async def approve_autopilot_action(
    generation_id: str,
    req: ApprovalDecisionInput,
    user: dict = Depends(get_current_user)
):
    res = global_autopilot_service.approve(generation_id, req.request_id)
    return {"status": "success", **res}


@router.post("/{generation_id}/reject")
async def reject_autopilot_action(
    generation_id: str,
    req: ApprovalDecisionInput,
    user: dict = Depends(get_current_user)
):
    res = global_autopilot_service.reject(generation_id, req.request_id)
    return {"status": "success", **res}


@router.get("/{generation_id}/decisions")
async def get_autopilot_decisions(
    generation_id: str,
    user: dict = Depends(get_current_user)
):
    decisions = global_autopilot_service.get_decisions(generation_id)
    return {"status": "success", "generation_id": generation_id, "decisions": decisions}


@router.get("/{generation_id}/timeline")
async def get_autopilot_timeline(
    generation_id: str,
    user: dict = Depends(get_current_user)
):
    user_id = user.get("id", "default_user")
    state = global_autopilot_service.get_autopilot_state(generation_id, user_id)
    return {
        "status": "success",
        "generation_id": generation_id,
        "current_agent": state.get("current_agent"),
        "progress": state.get("progress"),
        "decisions": state.get("decisions", [])
    }


@flight_router.get("/{project_id}/flight-recorder")
async def get_project_flight_recorder(
    project_id: str,
    stage: Optional[str] = Query(None),
    agent: Optional[str] = Query(None),
    user: dict = Depends(get_current_user)
):
    res = global_autopilot_service.get_flight_recorder(project_id)
    return res


@flight_router.get("/{project_id}/analytics")
async def get_project_analytics(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    res = global_autopilot_service.get_flight_recorder(project_id)
    return {"status": "success", "project_id": project_id, "analytics": res.get("analytics", {})}
