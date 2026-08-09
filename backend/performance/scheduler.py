"""
AIForge Quality Recovery Day 14 — Task Scheduler, DAG Dependency Concurrency & Backpressure
===========================================================================================
Provides TaskNode, DAG-based TaskScheduler, bounded resource semaphores (LLM, CPU, IO, SANDBOX, GIT),
backpressure queuing, task cancellation propagation, and deadline controls.
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, Any, List, Set, Callable, Optional
import logging

from backend.performance.config import global_performance_config

logger = logging.getLogger("aiforge.performance.scheduler")


class TaskNode:
    """Represents a node in a workflow DAG with dependencies and resource constraints."""

    def __init__(
        self,
        task_id: str,
        operation: Callable[[], Any],
        dependencies: Optional[List[str]] = None,
        timeout: float = 30.0,
        priority: int = 1,
        resource_class: str = "CPU"  # LLM, CPU, IO, SANDBOX, GIT
    ):
        self.id = task_id
        self.operation = operation
        self.dependencies = dependencies or []
        self.timeout = timeout
        self.priority = priority
        self.resource_class = resource_class
        self.status = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
        self.result: Any = None
        self.error: Optional[Exception] = None


class TaskScheduler:
    """
    DAG Task Scheduler executing independent tasks concurrently while respecting
    resource limits, dependencies, timeouts, backpressure, and cancellation.
    """

    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="aiforge_task")
        self._semaphores = {
            "LLM": threading.Semaphore(global_performance_config.MAX_CONCURRENT_LLM_CALLS),
            "CPU": threading.Semaphore(8),
            "IO": threading.Semaphore(8),
            "SANDBOX": threading.Semaphore(global_performance_config.MAX_CONCURRENT_TESTS),
            "GIT": threading.Semaphore(2),
        }
        self._cancel_flags: Dict[str, bool] = {}
        self._lock = threading.Lock()

    def run_dag(
        self,
        tasks: List[TaskNode],
        deadline: Optional[float] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a set of tasks respecting their DAG dependencies.
        Returns a map of task_id -> result.
        """
        req_id = request_id or "DAG"
        task_map: Dict[str, TaskNode] = {t.id: t for t in tasks}
        completed: Set[str] = set()
        failed: Set[str] = set()
        futures: Dict[str, Future] = {}
        t_start = time.time()

        logger.info(f"[{req_id}] TaskScheduler: Scheduling {len(tasks)} tasks in DAG execution mode.")

        while len(completed) + len(failed) < len(tasks):
            # Check deadline budget
            if deadline and time.time() > deadline:
                logger.warning(f"[{req_id}] TaskScheduler: Request deadline exceeded! Cancelling remaining tasks.")
                for tid, tnode in task_map.items():
                    if tnode.status == "PENDING":
                        tnode.status = "CANCELLED"
                        failed.add(tid)
                break

            # Find ready tasks whose dependencies have all completed successfully
            ready_tasks = [
                t for t in tasks
                if t.status == "PENDING"
                and all(dep in completed for dep in t.dependencies)
            ]

            if not ready_tasks and not futures:
                # Deadlock or unresolvable dependency failure
                logger.error(f"[{req_id}] TaskScheduler: DAG execution stalled or dependency failed.")
                for t in tasks:
                    if t.status == "PENDING":
                        t.status = "CANCELLED"
                        failed.add(t.id)
                break

            # Launch ready tasks
            for tnode in ready_tasks:
                tnode.status = "RUNNING"
                futures[tnode.id] = self._executor.submit(self._execute_node, tnode, req_id)

            # Wait briefly for any in-flight task to complete
            done_ids = []
            for tid, fut in list(futures.items()):
                if fut.done():
                    done_ids.append(tid)

            if not done_ids and futures:
                time.sleep(0.05)
                continue

            for tid in done_ids:
                fut = futures.pop(tid)
                tnode = task_map[tid]
                try:
                    res = fut.result()
                    tnode.result = res
                    tnode.status = "COMPLETED"
                    completed.add(tid)
                except Exception as ex:
                    tnode.error = ex
                    tnode.status = "FAILED"
                    failed.add(tid)
                    logger.error(f"[{req_id}] Task [{tid}] failed: {ex}")

        results = {t.id: t.result for t in tasks if t.status == "COMPLETED"}
        logger.info(f"[{req_id}] DAG execution finished in {round((time.time() - t_start)*1000, 2)}ms ({len(completed)} succeeded, {len(failed)} failed).")
        return results

    def _execute_node(self, node: TaskNode, request_id: str) -> Any:
        sem = self._semaphores.get(node.resource_class, self._semaphores["CPU"])
        acquired = sem.acquire(timeout=node.timeout)
        if not acquired:
            raise TimeoutError(f"Task {node.id} timed out waiting for resource class '{node.resource_class}'.")

        try:
            if self._cancel_flags.get(request_id, False):
                node.status = "CANCELLED"
                raise RuntimeError(f"Task {node.id} cancelled by request.")

            logger.info(f"[{request_id}] Executing Task [{node.id}] (Resource: {node.resource_class})...")
            return node.operation()
        finally:
            sem.release()

    def cancel_request(self, request_id: str) -> None:
        """Flags a request for cancellation across running tasks."""
        with self._lock:
            self._cancel_flags[request_id] = True
            logger.warning(f"[{request_id}] TaskScheduler: Cancellation requested!")


global_task_scheduler = TaskScheduler()
