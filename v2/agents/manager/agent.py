"""
AIForge V2 – Project Manager Agent Class
=======================================
Project Manager Agent executing task breakdown and sprint schedule generation.
"""

import json
import time
import logging
from typing import List, Dict, Any
from v2.agents.base_agent_v2 import BaseAgentV2
from v2.agents.protocol import AgentRole
from v2.agents.ceo.models import CEOProjectEvaluation
from v2.agents.manager.prompts import MANAGER_SYSTEM_PROMPT
from v2.agents.manager.models import TaskItem, TaskPriority, TaskStatusV2
from v2.logs.logger import global_v2_logger

_logger = logging.getLogger("aiforge.v2.manager")


class ProjectManagerAgentV2(BaseAgentV2):
    """
    Project Manager Agent V2: Decomposes CEO specifications into actionable sprint task schedules.
    """

    def __init__(self):
        super().__init__(
            role=AgentRole.PROJECT_MANAGER,
            system_prompt=MANAGER_SYSTEM_PROMPT
        )

    def generate_task_breakdown(self, eval_result: CEOProjectEvaluation) -> List[TaskItem]:
        started_at = time.perf_counter()
        _logger.info(f"ProjectManagerAgentV2: Breaking down tasks for project '{eval_result.project_name}' (Tier: {eval_result.complexity_tier.value})")

        input_text = (
            f"Project: {eval_result.project_name}\n"
            f"Complexity Tier: {eval_result.complexity_tier.value}\n"
            f"Required Teams: {', '.join(eval_result.required_teams)}\n"
            f"Prompt: {eval_result.client_prompt}"
        )

        raw_output = self.run(input_text)
        elapsed_ms = (time.perf_counter() - started_at) * 1000

        try:
            if "```json" in raw_output:
                json_str = raw_output.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_output:
                json_str = raw_output.split("```")[1].split("```")[0].strip()
            else:
                json_str = raw_output.strip()

            items = json.loads(json_str)
            tasks = [
                TaskItem(
                    task_id=it.get("task_id", f"task_{idx+1}"),
                    task_name=it.get("task_name", f"Task {idx+1}"),
                    description=it.get("description", "Execute task deliverable."),
                    assigned_agent=it.get("assigned_agent", "planner"),
                    dependencies=it.get("dependencies", []),
                    priority=TaskPriority(it.get("priority", "high").lower()),
                    estimated_time_hours=float(it.get("estimated_time_hours", 1.0))
                )
                for idx, it in enumerate(items)
            ]
        except Exception as exc:
            _logger.warning(f"ProjectManagerAgentV2: Failed to parse task list JSON ({exc}). Using structured template breakdown.")
            tasks = self._template_breakdown(eval_result)

        global_v2_logger.log_agent_action(
            agent_name="manager",
            input_text=input_text,
            output_text=f"Generated {len(tasks)} tasks.",
            execution_time_ms=elapsed_ms,
            metadata={"tasks_count": len(tasks), "assigned_agents": list(set(t.assigned_agent for t in tasks))}
        )

        return tasks

    def _template_breakdown(self, eval_result: CEOProjectEvaluation) -> List[TaskItem]:
        teams = eval_result.required_teams
        tasks = [
            TaskItem(
                task_id="task_1",
                task_name="Requirement Analysis",
                description="Produce 9-section requirements and user story discovery report.",
                assigned_agent="planner",
                dependencies=[],
                priority=TaskPriority.CRITICAL,
                estimated_time_hours=0.5
            ),
            TaskItem(
                task_id="task_2",
                task_name="Architecture & API Design",
                description="Design component topology, REST routes, schemas, and dependencies.",
                assigned_agent="architect",
                dependencies=["task_1"],
                priority=TaskPriority.CRITICAL,
                estimated_time_hours=0.5
            )
        ]

        task_counter = 3

        if "database" in teams:
            tasks.append(
                TaskItem(
                    task_id=f"task_{task_counter}",
                    task_name="Database Schema Design",
                    description="Generate SQL table schema script.",
                    assigned_agent="database",
                    dependencies=["task_2"],
                    priority=TaskPriority.HIGH,
                    estimated_time_hours=0.5
                )
            )
            db_task_id = f"task_{task_counter}"
            task_counter += 1
        else:
            db_task_id = "task_2"

        if "backend" in teams:
            tasks.append(
                TaskItem(
                    task_id=f"task_{task_counter}",
                    task_name="FastAPI Backend Development",
                    description="Implement REST routes and Pydantic validation models.",
                    assigned_agent="backend",
                    dependencies=["task_2", db_task_id],
                    priority=TaskPriority.HIGH,
                    estimated_time_hours=1.0
                )
            )
            backend_task_id = f"task_{task_counter}"
            task_counter += 1
        else:
            backend_task_id = "task_2"

        if "frontend" in teams:
            tasks.append(
                TaskItem(
                    task_id=f"task_{task_counter}",
                    task_name="React Frontend Development",
                    description="Develop modular React UI views and state components.",
                    assigned_agent="frontend",
                    dependencies=["task_2"],
                    priority=TaskPriority.HIGH,
                    estimated_time_hours=1.0
                )
            )
            frontend_task_id = f"task_{task_counter}"
            task_counter += 1
        else:
            frontend_task_id = "task_2"

        if "qa" in teams:
            tasks.append(
                TaskItem(
                    task_id=f"task_{task_counter}",
                    task_name="Integration Testing",
                    description="Generate pytest suite and test coverage validation.",
                    assigned_agent="qa",
                    dependencies=[backend_task_id, frontend_task_id],
                    priority=TaskPriority.MEDIUM,
                    estimated_time_hours=0.5
                )
            )
            qa_task_id = f"task_{task_counter}"
            task_counter += 1
        else:
            qa_task_id = backend_task_id

        if "devops" in teams or "deployment" in teams:
            tasks.append(
                TaskItem(
                    task_id=f"task_{task_counter}",
                    task_name="Docker Deployment Packaging",
                    description="Assemble Dockerfiles, docker-compose, and environment configs.",
                    assigned_agent="devops" if "devops" in teams else "deployment",
                    dependencies=[qa_task_id],
                    priority=TaskPriority.MEDIUM,
                    estimated_time_hours=0.5
                )
            )
            task_counter += 1

        if "documentation" in teams:
            tasks.append(
                TaskItem(
                    task_id=f"task_{task_counter}",
                    task_name="Technical Documentation",
                    description="Generate project README.md and installation guide.",
                    assigned_agent="documentation",
                    dependencies=["task_1"],
                    priority=TaskPriority.LOW,
                    estimated_time_hours=0.5
                )
            )

        return tasks


global_manager_agent_v2 = ProjectManagerAgentV2()
