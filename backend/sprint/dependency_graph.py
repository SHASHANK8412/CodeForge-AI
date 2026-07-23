"""
AIForge Sprint Dependency Graph
===============================
Enforces task execution order and dependency satisfaction:
- Backend tasks wait for Database Schema completion
- Frontend tasks wait for Backend API completion
- Documentation & Testing tasks wait for coding tasks
Identifies runnable tasks whose dependencies are all satisfied.
"""

import logging
from typing import Dict, Any, List, Set
from backend.sprint.task import SprintTask

_logger = logging.getLogger("aiforge.sprint")


class SprintDependencyGraph:
    """
    Manages task dependency resolution and topological execution ordering.
    """

    def __init__(self) -> None:
        self.tasks: Dict[str, SprintTask] = {}

    def add_task(self, task: SprintTask) -> None:
        self.tasks[task.task_id] = task

    def get_runnable_tasks(self) -> List[SprintTask]:
        """
        Returns list of tasks whose dependencies are all 'Completed' and whose status is 'Pending' or 'Retry'.
        """
        runnable = []
        for task_id, task in self.tasks.items():
            if task.status not in ["Pending", "Retry"]:
                continue

            # Check if all prerequisite dependencies are Completed
            deps_satisfied = True
            for dep_id in task.dependencies:
                if dep_id in self.tasks:
                    dep_task = self.tasks[dep_id]
                    if dep_task.status != "Completed":
                        deps_satisfied = False
                        break

            if deps_satisfied:
                runnable.append(task)

        return runnable

    def is_all_completed(self) -> bool:
        return all(t.status == "Completed" for t in self.tasks.values())
