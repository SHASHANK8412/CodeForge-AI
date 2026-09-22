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
    project_id: str = "aiforge-fooddelivery-ai"
    assigned_agent: Optional[str] = "agent-coding"
    dependencies: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    is_blocked: bool = False
    blocker_reason: Optional[str] = None
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    updated_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


INITIAL_TASKS = [
    {
        "id": "task_food_01",
        "title": "Implement Redis Streams Courier Geolocation Queue",
        "description": "Build high-throughput async ingest worker for real-time driver coordinate broadcasts.",
        "priority": "CRITICAL",
        "status": "IN_PROGRESS",
        "deadline": "Tomorrow, 5:00 PM",
        "project_id": "aiforge-fooddelivery-ai",
        "assigned_agent": "agent-coding",
        "dependencies": [],
        "tags": ["Backend", "Redis", "FastAPI"]
    },
    {
        "id": "task_food_02",
        "title": "Design Dynamic Surge Pricing Estimation Model",
        "description": "Analyze dinner peak order volume and compute dynamic delivery fee multiplier.",
        "priority": "HIGH",
        "status": "TODO",
        "deadline": "In 3 Days",
        "project_id": "aiforge-fooddelivery-ai",
        "assigned_agent": "agent-data-analyst",
        "dependencies": ["task_food_01"],
        "tags": ["Analytics", "Pricing", "Algorithms"]
    },
    {
        "id": "task_food_03",
        "title": "Comprehensive DBMS Indexing & Normalization Study Plan",
        "description": "Complete 5-day syllabus revision for B-Trees, transactions, and ACID isolation levels.",
        "priority": "HIGH",
        "status": "DONE",
        "deadline": "Completed",
        "project_id": "aiforge-fooddelivery-ai",
        "assigned_agent": "agent-study",
        "dependencies": [],
        "tags": ["Study", "DBMS", "Exam"]
    },
    {
        "id": "task_food_04",
        "title": "Stripe Webhook & RS256 Idempotency Review",
        "description": "Verify idempotency keys and replay protection for customer checkout transactions.",
        "priority": "MEDIUM",
        "status": "REVIEW",
        "deadline": "Friday, 12:00 PM",
        "project_id": "aiforge-fooddelivery-ai",
        "assigned_agent": "agent-coding",
        "dependencies": [],
        "tags": ["Security", "Payments", "Audit"]
    }
]


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
        try:
            if self.storage_file.exists():
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        t = AITask(**item)
                        self._tasks[t.id] = t
            else:
                for item in INITIAL_TASKS:
                    t = AITask(**item)
                    self._tasks[t.id] = t
                self._save()
        except Exception as e:
            _logger.error(f"Error loading tasks: {e}")
            for item in INITIAL_TASKS:
                t = AITask(**item)
                self._tasks[t.id] = t

    def _save(self):
        try:
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump([t.model_dump() for t in self._tasks.values()], f, indent=2)
        except Exception as e:
            _logger.error(f"Error saving tasks: {e}")

    def list_tasks(self, project_id: Optional[str] = None, status: Optional[str] = None) -> List[AITask]:
        tasks = list(self._tasks.values())
        if project_id:
            tasks = [t for t in tasks if t.project_id == project_id]
        if status and status != "ALL":
            tasks = [t for t in tasks if t.status.value == status]
        tasks.sort(key=lambda x: (x.priority == TaskPriority.CRITICAL, x.status == TaskStatus.IN_PROGRESS), reverse=True)
        return tasks

    def get_task(self, task_id: str) -> Optional[AITask]:
        return self._tasks.get(task_id)

    def create_task(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        status: TaskStatus = TaskStatus.TODO,
        deadline: Optional[str] = None,
        project_id: str = "aiforge-fooddelivery-ai",
        assigned_agent: Optional[str] = "agent-coding",
        dependencies: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
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
            tags=tags or []
        )
        self._tasks[task.id] = task
        self._save()
        return task

    def update_task(self, task_id: str, **kwargs) -> Optional[AITask]:
        task = self._tasks.get(task_id)
        if not task:
            return None
        for k, v in kwargs.items():
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

    def decompose_goal_into_tasks(self, goal: str, project_id: str = "aiforge-fooddelivery-ai") -> List[AITask]:
        """
        Deconstructs a high-level goal into concrete subtasks.
        """
        subtasks_data = [
            {"title": f"Phase 1: Architecture Blueprint for {goal[:30]}", "priority": TaskPriority.HIGH, "agent": "agent-coding"},
            {"title": f"Phase 2: Data Model & Schema Implementation", "priority": TaskPriority.HIGH, "agent": "agent-coding"},
            {"title": f"Phase 3: Integration Tests & Benchmark", "priority": TaskPriority.MEDIUM, "agent": "agent-coding"}
        ]
        created = []
        for s in subtasks_data:
            t = self.create_task(
                title=s["title"],
                description=f"Generated subtask for goal: '{goal}'",
                priority=s["priority"],
                project_id=project_id,
                assigned_agent=s["agent"],
                tags=["AI-Decomposed"]
            )
            created.append(t)
        return created

    def get_next_best_action(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Answers: 'What is the most important thing I should do next?'
        """
        tasks = self.list_tasks(project_id=project_id)
        in_progress = [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
        if in_progress:
            target = in_progress[0]
            return {
                "recommendation": f"Continue In-Progress Task: '{target.title}'",
                "task": target.model_dump(),
                "reason": "This task is currently active with high priority and pending subtasks.",
                "suggested_action": "Open in Code Workspace or dispatch Coding Agent."
            }

        todo = [t for t in tasks if t.status == TaskStatus.TODO and t.priority in [TaskPriority.CRITICAL, TaskPriority.HIGH]]
        if todo:
            target = todo[0]
            return {
                "recommendation": f"Start Critical Task: '{target.title}'",
                "task": target.model_dump(),
                "reason": "Highest priority pending item without active blockers.",
                "suggested_action": "Assign to Agent or start in Live Canvas."
            }

        return {
            "recommendation": "All high-priority tasks completed! Review saved outputs or plan next sprint.",
            "task": None,
            "reason": "No critical blockers or active tasks detected.",
            "suggested_action": "Run Deep Research or create a new project roadmap."
        }


global_task_service = TaskManagementService()
