"""
AIForge Day 84 Sprint Manager Agent
===================================
Master Sprint Manager Agent coordinating task decomposition, priority assignment,
dependency graph analysis, time estimation, Kanban board generation, velocity tracking,
and smart replanning upon scope changes.
"""

import logging
from typing import Dict, Any, List, Optional

from backend.project_management.task_splitter import TaskSplitter
from backend.project_management.estimator import TaskEstimator
from backend.project_management.dependency_graph import ProjectDependencyGraph
from backend.project_management.kanban import KanbanBoardGenerator
from backend.project_management.roadmap_generator import RoadmapGenerator
from backend.project_management.velocity import VelocityCalculator

_logger = logging.getLogger("aiforge.agents")


class EnterpriseSprintManagerAgent:
    """
    Agile Sprint Manager Agent coordinating Day 84 task management capabilities.
    """

    def __init__(self) -> None:
        self.splitter = TaskSplitter()
        self.estimator = TaskEstimator()
        self.dependency_graph = ProjectDependencyGraph()
        self.kanban_generator = KanbanBoardGenerator()
        self.roadmap_generator = RoadmapGenerator()
        self.velocity_calculator = VelocityCalculator()

    def plan_sprint_management(self, project_prompt: str) -> Dict[str, Any]:
        _logger.info(f"EnterpriseSprintManagerAgent planning sprint management for '{project_prompt}'...")

        # 1. Task Decomposition
        raw_tasks = self.splitter.decompose_project(project_prompt)

        # 2. Estimate effort & risk
        estimated_tasks = []
        for t in raw_tasks:
            est = self.estimator.estimate_task(t)
            t.update(est)
            estimated_tasks.append(t)

        # 3. Assign dependency graph
        tasks_with_deps = self.dependency_graph.assign_dependencies(estimated_tasks)

        # 4. Generate Kanban board
        kanban_board = self.kanban_generator.generate_kanban_board(tasks_with_deps)

        # 5. Generate Roadmap
        roadmap = self.roadmap_generator.generate_roadmap(tasks_with_deps)

        # 6. Calculate Velocity
        velocity = self.velocity_calculator.calculate_velocity(tasks_with_deps)

        return {
            "project_prompt": project_prompt,
            "tasks_count": len(tasks_with_deps),
            "tasks": tasks_with_deps,
            "kanban_board": kanban_board,
            "roadmap": roadmap,
            "velocity": velocity
        }

    def replan_on_scope_change(self, current_tasks: List[Dict[str, Any]], scope_change: str) -> Dict[str, Any]:
        return self.velocity_calculator.smart_replan(current_tasks, scope_change)


global_enterprise_sprint_manager = EnterpriseSprintManagerAgent()
