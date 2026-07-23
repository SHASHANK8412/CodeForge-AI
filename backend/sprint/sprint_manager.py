"""
AIForge Sprint Manager Agent
============================
Master Agile Sprint Manager Agent for Day 81:
- Breaks project requirements into structured SprintTask objects
- Assigns tasks to specialized agents (Database, Backend, Frontend, Testing, Documentation, DevOps)
- Enforces topological dependency graph ordering and conflict resolution
- Manages parallel scheduling, automated retry strategies, and backup agent delegation
- Generates live progress updates and comprehensive Sprint Completion Reports
"""

import time
import logging
from typing import Dict, Any, List, Optional
from backend.sprint.task import SprintTask
from backend.sprint.dependency_graph import SprintDependencyGraph
from backend.sprint.scheduler import SprintScheduler
from backend.sprint.progress_tracker import SprintProgressTracker
from backend.sprint.sprint_report import SprintReportGenerator

_logger = logging.getLogger("aiforge.sprint")


class SprintManagerAgent:
    """
    Master Agile Sprint Manager Agent coordinating multi-agent development sprints.
    """

    def __init__(self) -> None:
        self.dep_graph = SprintDependencyGraph()
        self.progress_tracker = SprintProgressTracker()
        self.report_generator = SprintReportGenerator()

    def plan_sprint_tasks(self, project_name: str = "Enterprise Platform") -> List[SprintTask]:
        """
        Breaks project into tasks with assigned agents, priorities, and dependency rules:
        - Backend waits for Database Schema
        - Frontend waits for Backend API
        - Documentation & Testing wait for coding agents
        """
        _logger.info(f"SprintManagerAgent: Planning Agile Sprint tasks for project '{project_name}'...")
        tasks = [
            SprintTask(
                task_id="TASK-101",
                description="Design & Initialize Database Schema",
                assigned_agent="Database Agent",
                priority="HIGH",
                estimated_time_seconds=8.0,
                dependencies=[],
                target_files=["backend/models/schema.py"]
            ),
            SprintTask(
                task_id="TASK-102",
                description="Implement Async FastAPI CRUD Controllers & Auth Routes",
                assigned_agent="Backend Agent",
                priority="HIGH",
                estimated_time_seconds=12.0,
                dependencies=["TASK-101"],
                target_files=["backend/routes/auth.py", "backend/routes/api.py"]
            ),
            SprintTask(
                task_id="TASK-103",
                description="Develop React Tailwind UI Components & State Context",
                assigned_agent="Frontend Agent",
                priority="MEDIUM",
                estimated_time_seconds=10.0,
                dependencies=["TASK-102"],
                target_files=["frontend/src/components/Dashboard.jsx", "frontend/src/api/config.js"]
            ),
            SprintTask(
                task_id="TASK-104",
                description="Execute Automated Pytest & Integration Test Suites",
                assigned_agent="Testing Agent",
                priority="HIGH",
                estimated_time_seconds=6.0,
                dependencies=["TASK-102", "TASK-103"],
                target_files=["tests/test_integration.py"]
            ),
            SprintTask(
                task_id="TASK-105",
                description="Generate API Documentation & System README",
                assigned_agent="Documentation Agent",
                priority="LOW",
                estimated_time_seconds=5.0,
                dependencies=["TASK-102", "TASK-103"],
                target_files=["README.md", "docs/API_REFERENCE.md"]
            ),
            SprintTask(
                task_id="TASK-106",
                description="Build Multi-stage Docker & GitHub Actions CI/CD Pipeline",
                assigned_agent="DevOps Agent",
                priority="MEDIUM",
                estimated_time_seconds=7.0,
                dependencies=["TASK-101"],
                target_files=["Dockerfile", ".github/workflows/ci.yml"]
            )
        ]

        self.dep_graph = SprintDependencyGraph()
        for t in tasks:
            self.dep_graph.add_task(t)

        return tasks

    async def execute_sprint(self, failure_task_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Executes full Agile Sprint:
        Task Creation -> Dependency Check -> Parallel Scheduler -> Retry Strategy -> Report Generation
        """
        _logger.info("SprintManagerAgent: Executing Agile Sprint workflow...")
        scheduler = SprintScheduler(self.dep_graph)
        completed_tasks = await scheduler.run_sprint(failure_task_ids=failure_task_ids)

        report = self.report_generator.generate_sprint_report(completed_tasks)
        progress = self.progress_tracker.get_progress_metrics(completed_tasks)

        return {
            "status": "success",
            "progress": progress,
            "report": report,
            "tasks": [t.to_dict() for t in completed_tasks]
        }


global_sprint_manager = SprintManagerAgent()
