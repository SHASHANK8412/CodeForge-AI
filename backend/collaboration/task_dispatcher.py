"""
Day 43 - Collaborative Multi-Agent Task Dispatcher
===================================================
Decomposes user requirements into independent, typed tasks for parallel agent execution.
"""

from typing import List, Dict, Any
from dataclasses import dataclass, field
import uuid


@dataclass
class Task:
    id: str
    target_agent: str  # frontend, backend, database, documentation, testing
    title: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, in_progress, completed, failed


class TaskDispatcher:
    """Decomposes user requirements into specialized agent tasks for all 8 team roles."""

    AGENT_ROLES = ["planner", "architect", "database", "backend", "frontend", "testing", "reviewer", "documentation"]

    def dispatch(self, user_requirements: str) -> List[Task]:
        task_id_prefix = str(uuid.uuid4())[:8]

        tasks = [
            Task(
                id=f"task-plan-{task_id_prefix}",
                target_agent="planner",
                title="Decompose Requirements & Scope",
                description=f"Analyze requirements and generate initial project plan for: '{user_requirements}'",
                dependencies=[]
            ),
            Task(
                id=f"task-arch-{task_id_prefix}",
                target_agent="architect",
                title="Design System Architecture & Stack",
                description=f"Produce technical architecture blueprint for: '{user_requirements}'",
                dependencies=[f"task-plan-{task_id_prefix}"]
            ),
            Task(
                id=f"task-db-{task_id_prefix}",
                target_agent="database",
                title="Design Database Schema & Models",
                description=f"Create database schema, tables, and migrations for: '{user_requirements}'",
                dependencies=[f"task-arch-{task_id_prefix}"]
            ),
            Task(
                id=f"task-be-{task_id_prefix}",
                target_agent="backend",
                title="Implement FastAPI REST API & Logic",
                description=f"Implement backend endpoints, services, and schemas for: '{user_requirements}'",
                dependencies=[f"task-db-{task_id_prefix}"]
            ),
            Task(
                id=f"task-fe-{task_id_prefix}",
                target_agent="frontend",
                title="Build React UI Components & Pages",
                description=f"Create interactive frontend components and API client for: '{user_requirements}'",
                dependencies=[f"task-be-{task_id_prefix}"]
            ),
            Task(
                id=f"task-test-{task_id_prefix}",
                target_agent="testing",
                title="Write Unit & Integration Test Suites",
                description=f"Create test suites verifying endpoints and database constraints for: '{user_requirements}'",
                dependencies=[f"task-be-{task_id_prefix}", f"task-fe-{task_id_prefix}"]
            ),
            Task(
                id=f"task-rev-{task_id_prefix}",
                target_agent="reviewer",
                title="Audit Code Quality & Perform Refactoring",
                description=f"Perform static analysis, security audit, and refactor code for: '{user_requirements}'",
                dependencies=[f"task-test-{task_id_prefix}"]
            ),
            Task(
                id=f"task-doc-{task_id_prefix}",
                target_agent="documentation",
                title="Generate Technical Specs & OpenAPI Docs",
                description=f"Produce architecture specification and README for: '{user_requirements}'",
                dependencies=[f"task-rev-{task_id_prefix}"]
            ),
        ]

        return tasks
