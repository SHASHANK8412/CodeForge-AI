"""
AIForge Distributed Monitoring Service
======================================
Monitors cluster health, CPU/RAM utilization, queue sizes, active tasks, failed jobs, and average task execution times.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from backend.distributed.node_manager import global_node_manager
from backend.distributed.task_queue import global_distributed_task_queue

_logger = logging.getLogger("aiforge.distributed.monitoring")


class ClusterMonitoringService:
    """
    Monitors cluster status and performance metrics.
    """

    def get_cluster_metrics(self) -> Dict[str, Any]:
        nodes = global_node_manager.list_nodes()
        tasks = global_distributed_task_queue.get_queue_status()

        online_nodes = [n for n in nodes if n["status"] == "ONLINE"]

        metrics = {
            "timestamp": time.time(),
            "cluster_health": ("NO_WORKERS" if not nodes else "HEALTHY" if len(online_nodes) == len(nodes) else "DEGRADED"),
            "active_worker_nodes": len(online_nodes),
            "total_worker_nodes": len(nodes),
            "cpu_utilization_pct": None,           # not measured
            "memory_utilization_pct": None,
            "queued_tasks_count": len(tasks),
            "running_tasks_count": sum(n.get("active_tasks_count", 0) for n in nodes),
            "failed_jobs_count": None,             # not tracked
            "average_task_duration": None,
            "auto_scaling_status": "NOT_IMPLEMENTED"
        }

        _logger.info(f"ClusterMonitoringService: Metrics compiled (Health: {metrics['cluster_health']}, Online: {len(online_nodes)}/{len(nodes)})")
        return metrics


global_cluster_monitoring_service = ClusterMonitoringService()
