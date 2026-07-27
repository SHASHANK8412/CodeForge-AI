"""
AIForge Distributed Task Queue
==============================
Priority-based distributed task queue supporting execution priorities: Critical, High, Normal, Low.
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.distributed.task_queue")


class TaskPriority:
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


class DistributedTaskQueue:
    """
    Priority queue managing distributed AI agent tasks.
    """

    def __init__(self) -> None:
        self.queue: List[Dict[str, Any]] = [
            {
                "task_id": "task_101",
                "project_name": "Food Delivery API",
                "agent_name": "Planner Agent",
                "priority": TaskPriority.HIGH,
                "priority_label": "High",
                "status": "QUEUED",
                "queued_at": time.time() - 120
            },
            {
                "task_id": "task_102",
                "project_name": "Food Delivery API",
                "agent_name": "Backend Agent",
                "priority": TaskPriority.NORMAL,
                "priority_label": "Normal",
                "status": "QUEUED",
                "queued_at": time.time() - 60
            }
        ]

    def enqueue_task(
        self,
        project_name: str,
        agent_name: str,
        priority_label: str = "Normal",
        task_payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        p_val = TaskPriority.NORMAL
        p_upper = priority_label.upper()
        if p_upper == "CRITICAL":
            p_val = TaskPriority.CRITICAL
        elif p_upper == "HIGH":
            p_val = TaskPriority.HIGH
        elif p_upper == "LOW":
            p_val = TaskPriority.LOW

        t_id = f"task_{int(time.time() * 1000)}"
        task = {
            "task_id": t_id,
            "project_name": project_name,
            "agent_name": agent_name,
            "priority": p_val,
            "priority_label": priority_label.capitalize(),
            "status": "QUEUED",
            "task_payload": task_payload or {},
            "queued_at": time.time()
        }

        self.queue.append(task)
        self.queue.sort(key=lambda t: t["priority"])
        _logger.info(f"DistributedTaskQueue: Enqueued task '{t_id}' for '{agent_name}' (Priority: {priority_label})")
        return task

    def dequeue_next_task(self) -> Optional[Dict[str, Any]]:
        for task in self.queue:
            if task["status"] == "QUEUED":
                task["status"] = "ASSIGNED"
                _logger.info(f"DistributedTaskQueue: Dequeued task '{task['task_id']}' ({task['agent_name']})")
                return task
        return None

    def get_queue_status(self) -> List[Dict[str, Any]]:
        return list(self.queue)


global_distributed_task_queue = DistributedTaskQueue()
