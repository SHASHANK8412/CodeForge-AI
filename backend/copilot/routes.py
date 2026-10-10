"""
AIForge Day 23 — AI Codebase Copilot REST API Routes
====================================================
Endpoints for:
- POST /api/projects/{projectId}/copilot/ask
- POST /api/projects/{projectId}/copilot/plan/{planId}/execute
- GET  /api/projects/{projectId}/copilot/search
- GET  /api/projects/{projectId}/copilot/history
- POST /api/projects/{projectId}/copilot/feedback
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user
from backend.copilot.service import global_codebase_copilot_service

day23_copilot_router = APIRouter(prefix="/api/projects", tags=["AI Codebase Copilot & Natural-Language Control"])


class CopilotAskPayload(BaseModel):
    prompt: str
    simulate_failure: bool = False


class CopilotFeedbackPayload(BaseModel):
    session_id: str
    message_id: str
    rating: str  # USEFUL, NOT_USEFUL, INCORRECT
    comment: Optional[str] = None


@day23_copilot_router.post("/{project_id}/copilot/ask")
async def ask_copilot(
    project_id: str,
    payload: CopilotAskPayload,
    user: dict = Depends(get_current_user)
):
    msg, steps = global_codebase_copilot_service.ask(project_id, payload.prompt, payload.simulate_failure)
    return {
        "status": "success",
        "message": msg.model_dump(),
        "progress_steps": [s.model_dump() for s in steps]
    }


@day23_copilot_router.post("/{project_id}/copilot/plan/{plan_id}/execute")
async def execute_copilot_plan(
    project_id: str,
    plan_id: str,
    simulate_failure: bool = False,
    user: dict = Depends(get_current_user)
):
    res = global_codebase_copilot_service.execute_plan(project_id, plan_id, simulate_failure)
    return {"status": "success", "result": res.model_dump()}


@day23_copilot_router.get("/{project_id}/copilot/search")
async def search_copilot_code(
    project_id: str,
    q: str = Query(...),
    user: dict = Depends(get_current_user)
):
    res = global_codebase_copilot_service.search_code(project_id, q)
    return {"status": "success", "results": res}


@day23_copilot_router.get("/{project_id}/copilot/history")
async def get_copilot_history(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    sess = global_codebase_copilot_service.get_or_create_session(project_id)
    return {"status": "success", "session": sess.model_dump()}


@day23_copilot_router.post("/{project_id}/copilot/feedback")
async def submit_copilot_feedback(
    project_id: str,
    payload: CopilotFeedbackPayload,
    user: dict = Depends(get_current_user)
):
    ok = global_codebase_copilot_service.submit_feedback(payload.session_id, payload.message_id, payload.rating, payload.comment)
    return {"status": "success", "accepted": ok}
