"""
FastAPI Routes for Day 80 AI Engineering Workspace
===================================================
Exposes REST APIs for workspace project management, live status, cross-project search,
global workspace chat, and project export.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from backend.workspace.manager import global_workspace_manager
from backend.workspace.state import global_workspace_state
from backend.workspace.events import global_event_bus

router = APIRouter(prefix="/api/v1/workspace", tags=["AI Engineering Workspace"])


class CreateProjectRequest(BaseModel):
    name: str
    description: Optional[str] = ""


class SwitchProjectRequest(BaseModel):
    project_id: str


class WorkspaceChatRequest(BaseModel):
    prompt: str


class ExportProjectRequest(BaseModel):
    project_id: str
    export_format: Optional[str] = "zip"


@router.post("/create")
async def create_workspace_project(req: CreateProjectRequest) -> Dict[str, Any]:
    """Creates a new independent software project inside the AI Engineering Workspace."""
    try:
        proj = global_workspace_manager.create_project(req.name, req.description)
        return {"status": "success", "project": proj}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects")
async def list_workspace_projects() -> Dict[str, Any]:
    """Lists all independent projects in the workspace."""
    projects = global_workspace_manager.get_all_projects()
    return {"status": "success", "total_projects": len(projects), "projects": projects}


@router.get("/project/{project_id}")
async def get_workspace_project(project_id: str) -> Dict[str, Any]:
    """Retrieves metadata and status for a specific project."""
    proj = global_workspace_manager.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return {"status": "success", "project": proj}


@router.delete("/delete/{project_id}")
async def delete_workspace_project(project_id: str) -> Dict[str, Any]:
    """Deletes an independent project from the workspace."""
    success = global_workspace_manager.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return {"status": "success", "message": f"Project '{project_id}' deleted."}


@router.post("/switch")
async def switch_workspace_project(req: SwitchProjectRequest) -> Dict[str, Any]:
    """Switches active workspace project context without losing session data."""
    try:
        proj = global_workspace_manager.switch_project(req.project_id)
        return {"status": "success", "active_project": proj}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status")
async def get_workspace_status() -> Dict[str, Any]:
    """Returns live agent statuses, active tasks queue, LLM token metrics, and recent events."""
    summary = global_workspace_state.get_status_summary()
    events = global_event_bus.get_all_events()[-15:]
    return {
        "status": "success",
        "summary": summary,
        "recent_events": events
    }


@router.get("/search")
async def global_workspace_search(q: str = Query(..., description="Search query string")) -> Dict[str, Any]:
    """Performs workspace-wide global search across code, components, and shared templates."""
    results = global_workspace_manager.global_search(q)
    return {"status": "success", "search_results": results}


@router.post("/chat")
async def workspace_global_chat(req: WorkspaceChatRequest) -> Dict[str, Any]:
    """Executes workspace-wide chat query or batch action across multiple projects."""
    try:
        res = global_workspace_manager.execute_workspace_chat(req.prompt)
        return {"status": "success", "chat_result": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
async def export_workspace_project(req: ExportProjectRequest) -> Dict[str, Any]:
    """Exports project source code, documentation, and configuration package."""
    proj = global_workspace_manager.get_project(req.project_id)
    if not proj:
        raise HTTPException(status_code=404, detail=f"Project '{req.project_id}' not found.")
    return {
        "status": "success",
        "project_id": req.project_id,
        "export_url": f"/exports/{proj['name']}_export.zip",
        "format": req.export_format
    }
