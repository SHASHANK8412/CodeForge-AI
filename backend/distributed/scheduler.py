"""
AIForge Distributed Scheduler
=============================
Distributed Master Scheduler assigning tasks to worker nodes, managing priority queues, and monitoring execution status.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from backend.distributed.task_queue import global_distributed_task_queue
from backend.distributed.node_manager import global_node_manager
from backend.distributed.load_balancer import global_load_balancer

_logger = logging.getLogger("aiforge.distributed.scheduler")


class DistributedScheduler:
    """
    Master Scheduler assigning tasks to worker nodes.
    """

    def submit_and_schedule(
        self,
        project_name: str,
        agent_name: str,
        priority_label: str = "Normal"
    ) -> Dict[str, Any]:
        # 1. Enqueue task
        task = global_distributed_task_queue.enqueue_task(project_name, agent_name, priority_label)

        # 2. Select worker via Load Balancer
        nodes = global_node_manager.list_nodes()
        worker = global_load_balancer.select_worker(nodes)

        if worker:
            task["assigned_worker"] = worker["node_id"]
            task["status"] = "ASSIGNED"
            worker["active_tasks_count"] += 1
            _logger.info(f"DistributedScheduler: Scheduled task '{task['task_id']}' on worker '{worker['node_id']}'")
        else:
            task["status"] = "QUEUED_WAITING_WORKER"

        return task

    def get_scheduler_status(self) -> Dict[str, Any]:
        tasks = global_distributed_task_queue.get_queue_status()
        nodes = global_node_manager.list_nodes()

        return {
            "timestamp": time.time(),
            "scheduler_status": "ACTIVE",
            "total_tasks_in_queue": len(tasks),
            "active_worker_nodes_count": len(nodes),
            "tasks": tasks
        }


global_distributed_scheduler = DistributedScheduler()
