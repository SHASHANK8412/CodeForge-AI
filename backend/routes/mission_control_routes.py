"""
AIForge REST API — Autonomous Computer, Mission Control & MCP Gateway
=====================================================================
Endpoints:
- GET /api/missions
- GET /api/missions/{mission_id}
- POST /api/missions/launch
- POST /api/missions/{mission_id}/approve
- POST /api/missions/{mission_id}/pause
- POST /api/missions/{mission_id}/resume
- GET /api/mcp/servers
- GET /api/mcp/tools
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, status
from pydantic import BaseModel, Field

from backend.sandbox.mission_control_service import global_mission_service, MissionRun
from backend.mcp.mcp_gateway import global_mcp_gateway

router = APIRouter(prefix="/api/missions", tags=["AIForge Mission Control & MCP"])


class LaunchMissionPayload(BaseModel):
    title: str
    goal: str
    project_id: Optional[str] = "aiforge-fooddelivery-ai"


class ApproveMissionPayload(BaseModel):
    approved: bool = True


@router.get("/templates")
def list_mission_templates():
    templates = global_mission_service.list_templates()
    return {
        "success": True,
        "count": len(templates),
        "templates": [t.model_dump() for t in templates]
    }


@router.get("")
def list_missions(project_id: Optional[str] = Query(None)):
    missions = global_mission_service.list_missions(project_id=project_id)
    return {
        "success": True,
        "count": len(missions),
        "missions": [m.model_dump() for m in missions]
    }


@router.get("/{mission_id}")
def get_mission(mission_id: str):
    m = global_mission_service.get_mission(mission_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Mission '{mission_id}' not found")
    return {
        "success": True,
        "mission": m.model_dump()
    }


@router.post("/launch", status_code=status.HTTP_201_CREATED)
def launch_mission(payload: LaunchMissionPayload):
    if not payload.title.strip() or not payload.goal.strip():
        raise HTTPException(status_code=400, detail="Title and Goal cannot be empty")

    mission = global_mission_service.launch_mission(
        title=payload.title,
        goal=payload.goal,
        project_id=payload.project_id or "aiforge-fooddelivery-ai"
    )
    return {
        "success": True,
        "mission": mission.model_dump()
    }


@router.post("/{mission_id}/approve")
def approve_mission_action(mission_id: str, payload: ApproveMissionPayload):
    m = global_mission_service.approve_mission(mission_id, approved=payload.approved)
    if not m:
        raise HTTPException(status_code=404, detail=f"Mission '{mission_id}' not found")
    return {
        "success": True,
        "mission": m.model_dump()
    }


@router.post("/{mission_id}/pause")
def pause_mission(mission_id: str):
    m = global_mission_service.pause_mission(mission_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Mission '{mission_id}' not found")
    return {
        "success": True,
        "mission": m.model_dump()
    }


@router.post("/{mission_id}/resume")
def resume_mission(mission_id: str):
    m = global_mission_service.resume_mission(mission_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Mission '{mission_id}' not found")
    return {
        "success": True,
        "mission": m.model_dump()
    }


@router.get("/mcp/servers")
def list_mcp_servers():
    servers = global_mcp_gateway.list_servers()
    return {
        "success": True,
        "count": len(servers),
        "servers": [s.model_dump() for s in servers]
    }


@router.get("/mcp/tools")
def list_mcp_tools(server_id: Optional[str] = Query(None)):
    tools = global_mcp_gateway.list_tools(server_id=server_id)
    return {
        "success": True,
        "count": len(tools),
        "tools": [t.model_dump() for t in tools]
    }
