"""
AIForge REST API — AI Agent Mode & Autonomous Task Engine
=========================================================
Endpoints:
- GET    /api/agents
- POST   /api/agents
- DELETE /api/agents/{agent_id}
- GET    /api/agents/tasks
- GET    /api/agents/tasks/{task_id}
- POST   /api/agents/tasks/launch
- POST   /api/agents/tasks/{task_id}/pause
- POST   /api/agents/tasks/{task_id}/resume
- POST   /api/agents/tasks/{task_id}/stop
- POST   /api/agents/tasks/{task_id}/approve
- POST   /api/agents/tasks/{task_id}/save-memory
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, status
from pydantic import BaseModel, Field

from backend.agents.agent_mode_service import (
    global_agent_mode_service,
    TaskStatus
)
from backend.memory.ai_memory_service import global_ai_memory_service, MemoryCategory, MemoryImportance, MemoryScope

router = APIRouter(prefix="/api/agents", tags=["AI Agent Mode & Task Orchestration"])


class CreateCustomAgentPayload(BaseModel):
    name: str
    description: str
    goal_placeholder: str
    system_instructions: str
    tools: List[str] = Field(default_factory=list)
    requires_human_approval: bool = False
    memory_access: bool = True
    project_access: bool = True
    max_steps: int = 6


class LaunchTaskPayload(BaseModel):
    agent_id: str
    goal: str
    project_id: Optional[str] = None
    memory_enabled: bool = True


class ApprovalPayload(BaseModel):
    approved: bool = True


@router.get("")
def list_agents():
    agents = global_agent_mode_service.list_agents()
    return {
        "success": True,
        "count": len(agents),
        "agents": [a.model_dump() for a in agents]
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_custom_agent(payload: CreateCustomAgentPayload):
    if not payload.name.strip() or not payload.description.strip():
        raise HTTPException(status_code=400, detail="Name and description are required")

    agent = global_agent_mode_service.create_custom_agent(
        name=payload.name,
        description=payload.description,
        goal_placeholder=payload.goal_placeholder,
        system_instructions=payload.system_instructions,
        tools=payload.tools,
        requires_human_approval=payload.requires_human_approval,
        memory_access=payload.memory_access,
        project_access=payload.project_access,
        max_steps=payload.max_steps
    )
    return {
        "success": True,
        "agent": agent.model_dump()
    }


@router.delete("/{agent_id}")
def delete_custom_agent(agent_id: str):
    success = global_agent_mode_service.delete_custom_agent(agent_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot delete built-in template or agent not found")
    return {
        "success": True,
        "deleted_id": agent_id
    }


@router.get("/tasks")
def list_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    project_id: Optional[str] = Query(None, description="Filter by project")
):
    tasks = global_agent_mode_service.list_tasks(status=status, project_id=project_id)
    return {
        "success": True,
        "count": len(tasks),
        "tasks": [t.model_dump() for t in tasks]
    }


@router.get("/tasks/{task_id}")
def get_task(task_id: str):
    task = global_agent_mode_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return {
        "success": True,
        "task": task.model_dump()
    }


@router.post("/tasks/launch", status_code=status.HTTP_202_ACCEPTED)
def launch_task(payload: LaunchTaskPayload):
    if not payload.goal.strip():
        raise HTTPException(status_code=400, detail="Goal cannot be empty")

    task = global_agent_mode_service.launch_task(
        agent_id=payload.agent_id,
        goal=payload.goal,
        project_id=payload.project_id,
        memory_enabled=payload.memory_enabled
    )
    return {
        "success": True,
        "task": task.model_dump()
    }


@router.post("/tasks/{task_id}/pause")
def pause_task(task_id: str):
    task = global_agent_mode_service.pause_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return {
        "success": True,
        "task": task.model_dump()
    }


@router.post("/tasks/{task_id}/resume")
def resume_task(task_id: str):
    task = global_agent_mode_service.resume_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return {
        "success": True,
        "task": task.model_dump()
    }


@router.post("/tasks/{task_id}/stop")
def stop_task(task_id: str):
    task = global_agent_mode_service.stop_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return {
        "success": True,
        "task": task.model_dump()
    }


@router.post("/tasks/{task_id}/approve")
def approve_task_action(task_id: str, payload: ApprovalPayload):
    task = global_agent_mode_service.approve_action(task_id, approved=payload.approved)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return {
        "success": True,
        "task": task.model_dump()
    }


@router.post("/tasks/{task_id}/save-memory")
def save_task_result_to_memory(task_id: str):
    task = global_agent_mode_service.get_task(task_id)
    if not task or not task.final_output:
        raise HTTPException(status_code=400, detail="Task not found or has no final output")

    memory_item = global_ai_memory_service.create_memory(
        title=f"Agent Output: {task.goal[:50]}",
        content=task.final_output[:1200],
        scope=MemoryScope.PROJECT if task.project_id else MemoryScope.PERSONAL,
        project_id=task.project_id,
        category=MemoryCategory.TASKS,
        importance=MemoryImportance.HIGH,
        source=f"Agent ({task.agent_name})",
        tags=[task.template_type, "Agent Output"]
    )
    return {
        "success": True,
        "memory": memory_item.model_dump()
    }
