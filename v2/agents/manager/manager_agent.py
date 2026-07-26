"""
AIForge V2 – Project Manager Agent
==================================
Project Manager Agent responsible for:
- Task Breakdown & Work Decomposition
- Dependency Graph Assembly
- Task Assignment & Agent Workflow Tracking
"""

import logging
from typing import List, Dict, Any
from v2.agents.base_agent_v2 import BaseAgentV2
from v2.agents.protocol import AgentRole, ProjectSpecification, TaskAssignment, TaskStatus

_logger = logging.getLogger("aiforge.v2.manager")


class ProjectManagerAgent(BaseAgentV2):
    """
    Project Manager Agent: Coordinates task distribution across technical departments.
    """

    def __init__(self):
        super().__init__(
            role=AgentRole.PROJECT_MANAGER,
            system_prompt="""
You are the Senior Project Manager of AIForge V2.
Your responsibility is to decompose project specifications into concrete actionable engineering tasks,
map task dependencies, and track deliverable completion.
"""
        )

    def plan_project_tasks(self, spec: ProjectSpecification) -> List[TaskAssignment]:
        _logger.info(f"ProjectManagerAgent: Decomposing project '{spec.name}' into departmental tasks...")

        tasks = [
            TaskAssignment(
                task_id=f"{spec.project_id}_task_1",
                project_id=spec.project_id,
                assigned_agent=AgentRole.PLANNER,
                title="Requirements & Functional Discovery Report",
                description="Produce full 9-section requirements and discovery report.",
                dependencies=[]
            ),
            TaskAssignment(
                task_id=f"{spec.project_id}_task_2",
                project_id=spec.project_id,
                assigned_agent=AgentRole.ARCHITECT,
                title="System Architecture & API Design",
                description="Design component topology, REST routes, schemas, and dependencies.",
                dependencies=[f"{spec.project_id}_task_1"]
            ),
            TaskAssignment(
                task_id=f"{spec.project_id}_task_3",
                project_id=spec.project_id,
                assigned_agent=AgentRole.FRONTEND,
                title="React Frontend Implementation",
                description="Develop modular React components and state views.",
                dependencies=[f"{spec.project_id}_task_2"]
            ),
            TaskAssignment(
                task_id=f"{spec.project_id}_task_4",
                project_id=spec.project_id,
                assigned_agent=AgentRole.BACKEND,
                title="FastAPI Backend Implementation",
                description="Implement FastAPI endpoints, Pydantic models, and security middleware.",
                dependencies=[f"{spec.project_id}_task_2"]
            ),
            TaskAssignment(
                task_id=f"{spec.project_id}_task_5",
                project_id=spec.project_id,
                assigned_agent=AgentRole.DATABASE,
                title="SQL Database Schema & Migrations",
                description="Generate production-grade SQL schema script.",
                dependencies=[f"{spec.project_id}_task_2"]
            ),
            TaskAssignment(
                task_id=f"{spec.project_id}_task_6",
                project_id=spec.project_id,
                assigned_agent=AgentRole.QA,
                title="Integration & Unit Testing Suite",
                description="Generate automated pytest and frontend unit tests.",
                dependencies=[f"{spec.project_id}_task_3", f"{spec.project_id}_task_4"]
            ),
            TaskAssignment(
                task_id=f"{spec.project_id}_task_7",
                project_id=spec.project_id,
                assigned_agent=AgentRole.REVIEWER,
                title="Code Quality & Security Audit",
                description="Conduct static code review and security vulnerability scan.",
                dependencies=[f"{spec.project_id}_task_6"]
            ),
            TaskAssignment(
                task_id=f"{spec.project_id}_task_8",
                project_id=spec.project_id,
                assigned_agent=AgentRole.DEPLOYMENT,
                title="Docker & Cloud Packaging",
                description="Assemble Dockerfiles, docker-compose, and deployment artifacts.",
                dependencies=[f"{spec.project_id}_task_7"]
            ),
        ]

        spec.tasks = tasks
        return tasks


global_manager_agent = ProjectManagerAgent()
