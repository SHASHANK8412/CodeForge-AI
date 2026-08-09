"""
AIForge Worker Node Framework
=============================
Worker node execution framework that registers with cluster schedulers, executes assigned AI agents, reports task status, and emits heartbeat signals.
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.distributed.worker")


class WorkerNode:
    """
    Worker node instance executing AI agents.
    """

    def __init__(self, node_id: str, host: str = "10.0.0.1", capacity: int = 4) -> None:
        self.node_id = node_id
        self.host = host
        self.capacity = capacity
        self.status = "ONLINE"
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.last_heartbeat = time.time()

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        t_id = task["task_id"]
        task["assigned_worker"] = self.node_id
        task["status"] = "RUNNING"
        task["started_at"] = time.time()
        
        self.active_tasks[t_id] = task
        self.last_heartbeat = time.time()

        _logger.info(f"WorkerNode [{self.node_id}]: Started executing task '{t_id}' ({task.get('agent_name')})")

        # Simulate agent completion
        task["status"] = "COMPLETED"
        task["completed_at"] = time.time()
        task["duration"] = f"{round(task['completed_at'] - task['started_at'], 2)}s"

        del self.active_tasks[t_id]
        return task

    def update_heartbeat(self) -> Dict[str, Any]:
        self.last_heartbeat = time.time()
        return {
            "node_id": self.node_id,
            "status": self.status,
            "active_tasks_count": len(self.active_tasks),
            "last_heartbeat": self.last_heartbeat
        }


global_worker_node_1 = WorkerNode("worker_node_1", host="10.0.0.12", capacity=4)
