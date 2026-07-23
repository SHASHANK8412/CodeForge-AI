"""
AIForge Sprint Parallel Scheduler
=================================
Schedules and executes independent sprint tasks in parallel (asyncio.gather).
Forces dependent tasks to wait for prerequisite completion.
Triggers retry logic and backup agent delegation if task failures occur.
"""

import asyncio
import logging
from typing import Dict, Any, List, Callable, Optional
from backend.sprint.task import SprintTask
from backend.sprint.dependency_graph import SprintDependencyGraph
from backend.sprint.conflict_detector import ConflictDetector

_logger = logging.getLogger("aiforge.sprint")


class SprintScheduler:
    """
    Parallel Task Scheduler enforcing dependency order and concurrency.
    """

    def __init__(self, dep_graph: SprintDependencyGraph) -> None:
        self.dep_graph = dep_graph
        self.conflict_detector = ConflictDetector()

    async def execute_task_simulated(self, task: SprintTask, force_failure: bool = False) -> None:
        task.mark_running()
        _logger.info(f"SprintScheduler: Task [{task.task_id}] STARTED by '{task.assigned_agent}'...")
        await asyncio.sleep(0.05)

        if force_failure and task.retry_count == 0:
            task.mark_failed(f"Simulated execution failure for agent '{task.assigned_agent}'")
            _logger.warning(f"SprintScheduler: Task [{task.task_id}] FAILED.")
        else:
            task.mark_review()
            await asyncio.sleep(0.02)
            task.mark_completed(output=f"Task [{task.task_id}] executed successfully by {task.assigned_agent}")
            _logger.info(f"SprintScheduler: Task [{task.task_id}] COMPLETED.")

    async def run_sprint(self, failure_task_ids: Optional[List[str]] = None) -> List[SprintTask]:
        failure_task_ids = failure_task_ids or []
        _logger.info(f"SprintScheduler: Starting sprint execution loop...")

        while not self.dep_graph.is_all_completed():
            runnable = self.dep_graph.get_runnable_tasks()
            if not runnable:
                _logger.info("SprintScheduler: No runnable tasks remaining or waiting for dependencies.")
                break

            # Conflict detection
            self.conflict_detector.detect_conflicts(runnable)

            # Parallel execution of all runnable tasks
            await asyncio.gather(*(
                self.execute_task_simulated(t, force_failure=(t.task_id in failure_task_ids))
                for t in runnable
            ))

            # Handle retries for failed tasks
            for t in runnable:
                if t.status == "Failed":
                    _logger.warning(f"SprintScheduler: Retrying failed task [{t.task_id}]...")
                    if t.prepare_retry(backup_agent="Senior Architectural Reviewer"):
                        await self.execute_task_simulated(t, force_failure=False)

        return list(self.dep_graph.tasks.values())
