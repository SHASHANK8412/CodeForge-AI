"""
AIForge REST API — Phase 3: Multi-Agent Collaboration & Team Intelligence
=========================================================================
Endpoints:
- GET  /api/multi-agent/agents
- GET  /api/multi-agent/missions
- GET  /api/multi-agent/missions/{mission_id}
- POST /api/multi-agent/missions/dispatch
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, status
from pydantic import BaseModel, Field

from backend.multi_agent.agent_registry import global_multi_agent_registry
from backend.multi_agent.multi_agent_orchestrator import global_multi_agent_orchestrator

router = APIRouter(prefix="/api/multi-agent", tags=["AIForge Multi-Agent Collaboration"])


class DispatchTeamPayload(BaseModel):
    objective: str
    project_id: Optional[str] = "aiforge-fooddelivery-ai"


@router.get("/agents")
def list_available_agents():
    agents = global_multi_agent_registry.list_agents()
    return {
        "success": True,
        "count": len(agents),
        "agents": [a.model_dump() for a in agents]
    }


@router.get("/missions")
def list_missions(project_id: Optional[str] = Query(None)):
    missions = global_multi_agent_orchestrator.list_missions(project_id=project_id)
    return {
        "success": True,
        "count": len(missions),
        "missions": [m.model_dump() for m in missions]
    }


@router.get("/missions/{mission_id}")
def get_mission(mission_id: str):
    m = global_multi_agent_orchestrator.get_mission(mission_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Collaborative mission '{mission_id}' not found")
    return {
        "success": True,
        "mission": m.model_dump()
    }


@router.post("/missions/dispatch", status_code=status.HTTP_201_CREATED)
def dispatch_team_mission(payload: DispatchTeamPayload):
    if not payload.objective.strip():
        raise HTTPException(status_code=400, detail="Objective cannot be empty")

    mission = global_multi_agent_orchestrator.dispatch_collaborative_mission(
        objective=payload.objective,
        project_id=payload.project_id or "aiforge-fooddelivery-ai"
    )
    return {
        "success": True,
        "mission": mission.model_dump()
    }
