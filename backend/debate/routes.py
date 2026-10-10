"""
AIForge Day 16 — Multi-Agent Debate REST API Routes
===================================================
Endpoints for:
- POST /api/debate/start
- GET  /api/debate/{projectId}/latest
- GET  /api/debate/{projectId}/history
- GET  /api/debate/{projectId}/adrs
- POST /api/debate/{projectId}/{debateId}/approve
- POST /api/debate/{projectId}/{debateId}/reject
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user
from backend.debate.service import global_debate_service

day16_debate_router = APIRouter(prefix="/api/debate", tags=["Multi-Agent Debate"])


class StartDebatePayload(BaseModel):
    project_id: str = "aiforge-demo"
    requirement: str
    generation_id: str = "aiforge-demo"
    force_debate: bool = True


@day16_debate_router.post("/start")
async def start_multi_agent_debate(
    payload: StartDebatePayload,
    user: dict = Depends(get_current_user)
):
    session = global_debate_service.run_project_debate(
        payload.project_id,
        payload.requirement,
        payload.generation_id,
        payload.force_debate
    )
    return {
        "status": "success",
        "session": session.model_dump(),
        "verdict": session.decision.model_dump() if session.decision else None
    }


@day16_debate_router.get("/{project_id}")
async def get_debate_verdict(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    session = global_debate_service.get_latest_session(project_id)
    return {
        "status": "success",
        "session": session.model_dump() if session else None,
        "verdict": session.decision.model_dump() if session and session.decision else None
    }


@day16_debate_router.get("/{project_id}/latest")
async def get_latest_debate_session(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    session = global_debate_service.get_latest_session(project_id)
    return {
        "status": "success",
        "session": session.model_dump() if session else None,
        "verdict": session.decision.model_dump() if session and session.decision else None
    }


@day16_debate_router.get("/{project_id}/history")
async def get_project_debate_history(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    sessions = global_debate_service.get_project_debates(project_id)
    return {"status": "success", "sessions": [s.model_dump() for s in sessions]}


@day16_debate_router.get("/{project_id}/adrs")
async def get_project_adrs(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    adrs = global_debate_service.get_all_adrs(project_id)
    return {"status": "success", "adrs": [a.model_dump() for a in adrs]}


@day16_debate_router.post("/{project_id}/{debate_id}/approve")
async def approve_debate_decision(
    project_id: str,
    debate_id: str,
    user: dict = Depends(get_current_user)
):
    success = global_debate_service.approve_decision(project_id, debate_id)
    return {"status": "success", "approved": success}


@day16_debate_router.post("/{project_id}/{debate_id}/reject")
async def reject_debate_decision(
    project_id: str,
    debate_id: str,
    user: dict = Depends(get_current_user)
):
    success = global_debate_service.reject_decision(project_id, debate_id)
    return {"status": "success", "rejected": success}
