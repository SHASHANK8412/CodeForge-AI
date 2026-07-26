"""
AIForge V2 – Orchestration Events
==================================
Event definitions for CEO, Project Manager, Planner, Architect, and Coder agent workflow transitions.
"""

from typing import Dict, Any
from pydantic import BaseModel


class CEOEvaluatedEvent(BaseModel):
    project_name: str
    complexity_tier: str
    complexity_score: float
    required_teams: list[str]


class TasksGeneratedEvent(BaseModel):
    project_id: str
    total_tasks: int
    task_ids: list[str]


class PlannerCompletedEvent(BaseModel):
    project_id: str
    markdown_report: str
