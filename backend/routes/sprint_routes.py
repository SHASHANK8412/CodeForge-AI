"""
AIForge REST API — 3-Day Sprint (Computer Agent & Intelligence Platform)
========================================================================
Endpoints:
- GET  /api/computer-agent/sessions
- GET  /api/computer-agent/sessions/{session_id}
- POST /api/computer-agent/sessions
- GET  /api/intelligence/overview
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, status
from pydantic import BaseModel, Field

from backend.computer_agent.browser_agent import global_computer_agent
from backend.intelligence.eval_engine import global_eval_engine

router = APIRouter(tags=["AIForge 3-Day Sprint (Computer Agent & Intelligence)"])


class CreateSessionPayload(BaseModel):
    goal: str
    target_url: Optional[str] = "https://fastapi.tiangolo.com"


@router.get("/api/computer-agent/sessions")
def list_browser_sessions():
    sessions = global_computer_agent.list_sessions()
    return {
        "success": True,
        "count": len(sessions),
        "sessions": [s.model_dump() for s in sessions]
    }


@router.get("/api/computer-agent/sessions/{session_id}")
def get_browser_session(session_id: str):
    s = global_computer_agent.get_session(session_id)
    if not s:
        raise HTTPException(status_code=404, detail=f"Browser session '{session_id}' not found")
    return {
        "success": True,
        "session": s.model_dump()
    }


@router.post("/api/computer-agent/sessions", status_code=status.HTTP_201_CREATED)
def create_browser_session(payload: CreateSessionPayload):
    if not payload.goal.strip():
        raise HTTPException(status_code=400, detail="Goal cannot be empty")

    s = global_computer_agent.create_browser_session(
        goal=payload.goal,
        target_url=payload.target_url or "https://fastapi.tiangolo.com"
    )
    return {
        "success": True,
        "session": s.model_dump()
    }


@router.get("/api/intelligence/overview")
def get_intelligence_overview():
    return {
        "success": True,
        "intelligence": global_eval_engine.get_intelligence_overview()
    }
