"""
FastAPI Routes for Day 27 Multi-Project Workspace & Agent Scheduling
======================================================================
Exposes REST APIs for workspace project management, shared agent pool scheduling, portfolio dashboard, resource allocation, and notifications.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from backend.workspace.workspace_manager import global_workspace_manager
from backend.workspace.scheduler import global_agent_scheduler
from backend.workspace.portfolio import global_portfolio_dashboard
from backend.workspace.notifications import global_notification_manager
from backend.workspace.resource_manager import global_resource_manager
from backend.workspace.priorities import global_priority_manager
from backend.workspace.analytics import global_workspace_analytics
from backend.workspace.state import global_workspace_state
from backend.workspace.events import global_event_bus

# Create two routers: legacy/prefixed router and top-level router for spec compatibility
router = APIRouter(tags=["Multi-Project Workspace"])


class CreateProjectRequest(BaseModel):
    name: str
    description: Optional[str] = ""


class SwitchProjectRequest(BaseModel):
    project_id: str


class ScheduleTaskRequest(BaseModel):
    project_id: str
    project_name: str
    task_name: str
    required_role: Optional[str] = "Any"
    priority: Optional[str] = "High"


class ResourceUpdateRequest(BaseModel):
    project_id: str
    llm_model: Optional[str] = None
    cpu_limit: Optional[str] = None
    memory_limit: Optional[str] = None
    max_concurrent_agents: Optional[int] = None


class PriorityUpdateRequest(BaseModel):
    project_id: str
    priority: str


class ReusePatternRequest(BaseModel):
    pattern_id: str
    target_project_id: str


@router.post("/workspace/create")
@router.post("/api/v1/workspace/create")
async def create_workspace_project(req: CreateProjectRequest) -> Dict[str, Any]:
    """Creates a new independent software project inside the AI Engineering Workspace."""
    try:
        proj = global_workspace_manager.create_project(req.name, req.description)
        return {"status": "success", "project": proj}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspace/projects")
@router.get("/api/v1/workspace/projects")
async def list_workspace_projects() -> Dict[str, Any]:
    """Lists all independent projects in the multi-project workspace."""
    projects = global_workspace_manager.get_all_projects()
    return {"status": "success", "total_projects": len(projects), "projects": projects}


@router.post("/workspace/switch")
@router.post("/api/v1/workspace/switch")
async def switch_workspace_project(req: SwitchProjectRequest) -> Dict[str, Any]:
    """Switches active workspace project context without losing state or session data."""
    try:
        proj = global_workspace_manager.switch_project(req.project_id)
        return {"status": "success", "active_project": proj}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/workspace/dashboard")
@router.get("/api/v1/workspace/dashboard")
async def get_portfolio_dashboard() -> Dict[str, Any]:
    """Retrieves portfolio-level dashboard overview: projects, active agents, running/failed tasks, health & completion %."""
    dashboard = global_workspace_manager.get_portfolio_overview()
    return {"status": "success", "dashboard": dashboard}


@router.get("/workspace/resources")
@router.get("/api/v1/workspace/resources")
async def get_workspace_resources(project_id: Optional[str] = None) -> Dict[str, Any]:
    """Retrieves LLM models, CPU, memory, plugins, and execution queue resource allocations."""
    if project_id:
        resources = global_resource_manager.get_resource_allocation(project_id)
    else:
        resources = global_resource_manager.get_all_resource_allocations()
    return {"status": "success", "resources": resources}


@router.post("/workspace/resources/update")
async def update_workspace_resources(req: ResourceUpdateRequest) -> Dict[str, Any]:
    """Updates resource limits and model assignments for a specific project."""
    updates = {k: v for k, v in req.dict().items() if v is not None and k != "project_id"}
    updated = global_resource_manager.update_resource_allocation(req.project_id, updates)
    return {"status": "success", "updated_resources": updated}


@router.get("/workspace/scheduler")
async def get_agent_scheduler_status() -> Dict[str, Any]:
    """Retrieves current agent pool statuses and cross-project task scheduling queues."""
    status = global_agent_scheduler.get_scheduler_status()
    return {"status": "success", "scheduler": status}


@router.post("/workspace/schedule/task")
async def schedule_agent_task(req: ScheduleTaskRequest) -> Dict[str, Any]:
    """Schedules a task to the shared AI agent pool across projects."""
    task = global_agent_scheduler.add_task_to_queue(
        project_id=req.project_id,
        project_name=req.project_name,
        task_name=req.task_name,
        required_role=req.required_role,
        priority=req.priority
    )
    return {"status": "success", "scheduled_task": task}


@router.get("/workspace/notifications")
async def get_workspace_notifications(project_id: Optional[str] = None, unread_only: bool = False) -> Dict[str, Any]:
    """Returns milestone and system notifications across workspace projects."""
    notifs = global_notification_manager.get_notifications(project_id=project_id, unread_only=unread_only)
    return {"status": "success", "notifications": notifs}


@router.get("/workspace/priorities")
async def get_workspace_priorities() -> Dict[str, Any]:
    """Returns project priority rankings and allowed priority levels."""
    priorities = global_priority_manager.get_all_priorities()
    return {"status": "success", "priorities": priorities}


@router.post("/workspace/priorities/update")
async def update_workspace_priority(req: PriorityUpdateRequest) -> Dict[str, Any]:
    """Updates project priority ranking."""
    try:
        res = global_priority_manager.set_project_priority(req.project_id, req.priority)
        return {"status": "success", "priority_update": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/workspace/analytics")
async def get_workspace_analytics_summary() -> Dict[str, Any]:
    """Returns cross-project learning summaries and shared pattern analytics."""
    summary = global_workspace_analytics.get_analytics_summary()
    return {"status": "success", "analytics": summary}


@router.post("/workspace/learning/reuse")
async def reuse_knowledge_pattern(req: ReusePatternRequest) -> Dict[str, Any]:
    """Reuses an established architectural or code pattern across projects."""
    try:
        res = global_workspace_manager.reuse_module_across_projects(req.target_project_id, req.pattern_id)
        return {"status": "success", "result": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
