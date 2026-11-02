"""
AIForge REST API — AI Task Management Engine
============================================
Endpoints:
- GET /api/tasks
- POST /api/tasks
- PUT /api/tasks/{task_id}
- DELETE /api/tasks/{task_id}
- POST /api/tasks/decompose
- GET /api/tasks/next-best-action
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, status
from pydantic import BaseModel, Field

from backend.tasks.task_management_service import (
    global_task_service,
    TaskPriority,
    TaskStatus,
    AITask
)

router = APIRouter(prefix="/api/tasks", tags=["AI Task Management"])


class CreateTaskPayload(BaseModel):
    title: str
    description: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.TODO
    deadline: Optional[str] = None
    project_id: str = "aiforge-fooddelivery-ai"
    assigned_agent: Optional[str] = "agent-coding"
    dependencies: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class UpdateTaskPayload(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    deadline: Optional[str] = None
    assigned_agent: Optional[str] = None
    tags: Optional[List[str]] = None


class DecomposePayload(BaseModel):
    goal: str
    project_id: Optional[str] = "aiforge-fooddelivery-ai"


@router.get("")
def list_tasks(
    project_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    tasks = global_task_service.list_tasks(project_id=project_id, status=status)
    return {
        "success": True,
        "count": len(tasks),
        "tasks": [t.model_dump() for t in tasks]
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_task(payload: CreateTaskPayload):
    if not payload.title.strip():
        raise HTTPException(status_code=400, detail="Task title cannot be empty")
    t = global_task_service.create_task(
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        status=payload.status,
        deadline=payload.deadline,
        project_id=payload.project_id,
        assigned_agent=payload.assigned_agent,
        dependencies=payload.dependencies,
        tags=payload.tags
    )
    return {
        "success": True,
        "task": t.model_dump()
    }


@router.put("/{task_id}")
def update_task(task_id: str, payload: UpdateTaskPayload):
    t = global_task_service.update_task(task_id=task_id, **payload.model_dump(exclude_unset=True))
    if not t:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return {
        "success": True,
        "task": t.model_dump()
    }


@router.delete("/{task_id}")
def delete_task(task_id: str):
    success = global_task_service.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return {
        "success": True,
        "deleted_id": task_id
    }


@router.post("/decompose")
def decompose_goal(payload: DecomposePayload):
    if not payload.goal.strip():
        raise HTTPException(status_code=400, detail="Goal cannot be empty")
    tasks = global_task_service.decompose_goal_into_tasks(goal=payload.goal, project_id=payload.project_id or "aiforge-fooddelivery-ai")
    return {
        "success": True,
        "decomposed_tasks": [t.model_dump() for t in tasks]
    }


@router.get("/next-best-action")
def get_next_best_action(project_id: Optional[str] = Query(None)):
    action = global_task_service.get_next_best_action(project_id=project_id)
    return {
        "success": True,
        "action": action
    }
