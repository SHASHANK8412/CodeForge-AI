"""
AIForge V2 – Inter-Agent Communication Protocol & Contracts
=============================================================
Defines standard schemas for CEO, Manager, Architect, Coder, QA, and DevOps communication.
"""

import time
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    CEO = "ceo"
    PROJECT_MANAGER = "manager"
    PLANNER = "planner"
    ARCHITECT = "architect"
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    DEVOPS = "devops"
    QA = "qa"
    REVIEWER = "reviewer"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    LEARNING = "learning"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentMessage(BaseModel):
    message_id: str
    sender: AgentRole
    recipient: AgentRole
    task_type: str
    payload: Dict[str, Any]
    timestamp: float = Field(default_factory=time.time)


class TaskAssignment(BaseModel):
    task_id: str
    project_id: str
    assigned_agent: AgentRole
    title: str
    description: str
    dependencies: List[str] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result_data: Optional[Dict[str, Any]] = None


class ProjectSpecification(BaseModel):
    project_id: str
    name: str
    client_prompt: str
    complexity_score: float = 5.0
    allocated_agents: List[AgentRole] = Field(default_factory=list)
    estimated_timeline_hours: float = 1.0
    tasks: List[TaskAssignment] = Field(default_factory=list)
