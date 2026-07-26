"""
AIForge V2 – Project Manager Data Models
=========================================
Task Models capturing:
Task ID, Task Name, Description, Assigned Agent, Dependencies, Priority, Estimated Time, Status, Progress.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatusV2(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskItem(BaseModel):
    task_id: str
    task_name: str
    description: str
    assigned_agent: str
    dependencies: List[str] = Field(default_factory=list)
    priority: TaskPriority = TaskPriority.HIGH
    estimated_time_hours: float = 1.0
    status: TaskStatusV2 = TaskStatusV2.PENDING
    progress_pct: float = 0.0
