"""
AIForge REST API — Tasks
========================
The signed-in user's task list. Every task belongs to the user who created it; someone else's task
answers 404.

Endpoints:
- GET /api/tasks
- POST /api/tasks
- PUT /api/tasks/{task_id}
- DELETE /api/tasks/{task_id}
- GET /api/tasks/next-best-action
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.auth.dependencies import get_current_user
from backend.auth.ownership import user_id_of
from backend.tasks.task_management_service import TaskPriority, TaskStatus, global_task_service

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


class CreateTaskPayload(BaseModel):
    title: str
    description: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.TODO
    deadline: Optional[str] = None
    project_id: Optional[str] = None
    assigned_agent: Optional[str] = None
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


def _own_task(task_id: str, user: dict):
    task = global_task_service.get_task(task_id, user_id_of(user))
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return task


@router.get("")
def list_tasks(
    project_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    user: dict = Depends(get_current_user),
):
    tasks = global_task_service.list_tasks(user_id_of(user), project_id=project_id, status=status)
    return {
        "success": True,
        "count": len(tasks),
        "tasks": [t.model_dump() for t in tasks]
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_task(payload: CreateTaskPayload, user: dict = Depends(get_current_user)):
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
        tags=payload.tags,
        owner_id=user_id_of(user),
    )
    return {
        "success": True,
        "task": t.model_dump()
    }


@router.get("/next-best-action")
def get_next_best_action(project_id: Optional[str] = Query(None), user: dict = Depends(get_current_user)):
    action = global_task_service.get_next_best_action(user_id_of(user), project_id=project_id)
    return {
        "success": True,
        "action": action
    }


@router.put("/{task_id}")
def update_task(task_id: str, payload: UpdateTaskPayload, user: dict = Depends(get_current_user)):
    _own_task(task_id, user)
    t = global_task_service.update_task(task_id=task_id, **payload.model_dump(exclude_unset=True))
    return {
        "success": True,
        "task": t.model_dump()
    }


@router.delete("/{task_id}")
def delete_task(task_id: str, user: dict = Depends(get_current_user)):
    _own_task(task_id, user)
    global_task_service.delete_task(task_id)
    return {
        "success": True,
        "deleted_id": task_id
    }
