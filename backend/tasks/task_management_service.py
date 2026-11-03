"""
AIForge AI-Powered Task Management Engine
=========================================
Manages task decomposition, dependency graphing, agent assignment, blocker detection,
and AI-recommended next best actions.
"""

import time
import uuid
import json
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field
from pathlib import Path

_logger = logging.getLogger("aiforge.tasks.service")


class TaskPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TaskStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    DONE = "DONE"


class AITask(BaseModel):
    id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    title: str
    description: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.TODO
    deadline: Optional[str] = None
    project_id: Optional[str] = None
    owner_id: Optional[str] = None  # the user who created the task
    assigned_agent: Optional[str] = "agent-coding"
    dependencies: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    is_blocked: bool = False
    blocker_reason: Optional[str] = None
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    updated_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


class TaskManagementService:
    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            self.storage_dir = Path(__file__).resolve().parent.parent / "data" / "tasks"
        
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_file = self.storage_dir / "tasks_store.json"
        self._tasks: Dict[str, AITask] = {}
        self._load()

    def _load(self):
        if not self.storage_file.exists():
            return
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    if not item.get("owner_id"):
                        continue          # sample tasks from earlier versions belong to nobody
                    t = AITask(**item)
                    self._tasks[t.id] = t
        except Exception as e:
            _logger.error(f"Error loading tasks: {e}")

    def _save(self):
        try:
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump([t.model_dump() for t in self._tasks.values()], f, indent=2)
        except Exception as e:
            _logger.error(f"Error saving tasks: {e}")

    def list_tasks(self, owner_id: str, project_id: Optional[str] = None, status: Optional[str] = None) -> List[AITask]:
        tasks = [t for t in self._tasks.values() if t.owner_id == owner_id]
        if project_id:
            tasks = [t for t in tasks if t.project_id == project_id]
        if status and status != "ALL":
            tasks = [t for t in tasks if t.status.value == status]
        tasks.sort(key=lambda x: (x.priority == TaskPriority.CRITICAL, x.status == TaskStatus.IN_PROGRESS), reverse=True)
        return tasks

    def get_task(self, task_id: str, owner_id: str) -> Optional[AITask]:
        task = self._tasks.get(task_id)
        return task if task is not None and task.owner_id == owner_id else None

    def create_task(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        status: TaskStatus = TaskStatus.TODO,
        deadline: Optional[str] = None,
        project_id: Optional[str] = None,
        assigned_agent: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        owner_id: Optional[str] = None,
    ) -> AITask:
        task = AITask(
            title=title.strip(),
            description=description.strip(),
            priority=priority,
            status=status,
            deadline=deadline,
            project_id=project_id,
            assigned_agent=assigned_agent,
            dependencies=dependencies or [],
            tags=tags or [],
            owner_id=owner_id,
        )
        self._tasks[task.id] = task
        self._save()
        return task

    def update_task(self, task_id: str, **kwargs) -> Optional[AITask]:
        task = self._tasks.get(task_id)
        if not task:
            return None
        for k, v in kwargs.items():
            if k in ("id", "owner_id"):
                continue
            if hasattr(task, k) and v is not None:
                setattr(task, k, v)
        task.updated_at = time.strftime("%Y-%m-%d %H:%M:%S")
        self._save()
        return task

    def delete_task(self, task_id: str) -> bool:
        if task_id in self._tasks:
            del self._tasks[task_id]
            self._save()
            return True
        return False

    def get_next_best_action(self, owner_id: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Answers 'What should I do next?' from the user's own tasks: the first task in progress, otherwise the
        first critical or high-priority task still to do.
        """
        tasks = self.list_tasks(owner_id, project_id=project_id)
        in_progress = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
        if in_progress:
            target = in_progress[0]
            return {
                "recommendation": f"Continue In-Progress Task: '{target.title}'",
                "task": target.model_dump(),
                "reason": "This task is already in progress.",
                "suggested_action": "Finish it before starting something new."
            }

        todo = [t for t in tasks if t.status == TaskStatus.TODO and t.priority in [TaskPriority.CRITICAL, TaskPriority.HIGH]]
        if todo:
            target = todo[0]
            return {
                "recommendation": f"Start Critical Task: '{target.title}'",
                "task": target.model_dump(),
                "reason": "It is the highest-priority task still to do.",
                "suggested_action": "Move it to in progress when you start."
            }

        return {
            "recommendation": "No task is in progress and no critical or high-priority task is waiting.",
            "task": None,
            "reason": "Nothing urgent in your task list.",
            "suggested_action": "Add tasks or pick a lower-priority one."
        }


global_task_service = TaskManagementService()
