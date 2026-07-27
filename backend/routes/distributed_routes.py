"""
FastAPI Routes for Day 40 AIForge Cloud Platform & Distributed Multi-Agent Execution
======================================================================================
Exposes REST APIs for cluster worker registration, task submission & priority scheduling, heartbeat updates, fault tolerance monitoring, cloud deployment profiles, and distributed system dashboards.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from backend.distributed.node_manager import global_node_manager
from backend.distributed.task_queue import global_distributed_task_queue
from backend.distributed.scheduler import global_distributed_scheduler
from backend.distributed.monitoring import global_cluster_monitoring_service
from backend.distributed.heartbeat import global_heartbeat_monitor
from backend.distributed.load_balancer import global_load_balancer

router = APIRouter(tags=["AIForge Cloud & Distributed Execution Engine"])


class RegisterWorkerInput(BaseModel):
    node_id: str
    host: Optional[str] = "10.0.0.20"
    capacity: Optional[int] = 4
    cloud_provider: Optional[str] = "AWS EKS"


class SubmitTaskInput(BaseModel):
    project_name: str
    agent_name: str
    priority_label: Optional[str] = "Normal"  # Critical, High, Normal, Low


class WorkerHeartbeatInput(BaseModel):
    node_id: str


@router.post("/cluster/register")
@router.post("/api/v1/cluster/register")
async def register_worker_node(req: RegisterWorkerInput) -> Dict[str, Any]:
    """Registers a new worker node with the distributed cluster."""
    try:
        node = global_node_manager.register_node(
            node_id=req.node_id,
            host=req.host or "10.0.0.20",
            capacity=req.capacity or 4,
            cloud_provider=req.cloud_provider or "AWS EKS"
        )
        return {"status": "success", "worker_node": node}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/cluster/nodes")
@router.get("/api/v1/cluster/nodes")
async def list_cluster_nodes() -> Dict[str, Any]:
    """Retrieves all registered worker nodes and their operational status."""
    nodes = global_node_manager.list_nodes()
    cloud_profiles = global_node_manager.get_cloud_deployment_profiles()
    return {"status": "success", "nodes_count": len(nodes), "nodes": nodes, "cloud_profiles": cloud_profiles}


@router.post("/tasks/submit")
@router.post("/api/v1/tasks/submit")
async def submit_distributed_task(req: SubmitTaskInput) -> Dict[str, Any]:
    """Submits an agent task for priority queuing and load-balanced worker scheduling."""
    try:
        task = global_distributed_scheduler.submit_and_schedule(
            project_name=req.project_name,
            agent_name=req.agent_name,
            priority_label=req.priority_label or "Normal"
        )
        return {"status": "success", "scheduled_task": task}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks/status")
@router.get("/api/v1/tasks/status")
async def get_distributed_tasks_status() -> Dict[str, Any]:
    """Retrieves current task queue status and assigned workers."""
    queue = global_distributed_task_queue.get_queue_status()
    return {"status": "success", "total_tasks": len(queue), "tasks": queue}


@router.get("/scheduler")
@router.get("/api/v1/scheduler")
async def get_scheduler_metrics() -> Dict[str, Any]:
    """Retrieves Master Scheduler status and queued tasks."""
    sched_status = global_distributed_scheduler.get_scheduler_status()
    return {"status": "success", "scheduler": sched_status}


@router.get("/monitoring")
@router.get("/api/v1/monitoring")
async def get_cluster_monitoring_metrics() -> Dict[str, Any]:
    """Retrieves cluster monitoring metrics: CPU/RAM utilization, queue sizes, active tasks, failed jobs."""
    metrics = global_cluster_monitoring_service.get_cluster_metrics()
    return {"status": "success", "monitoring_metrics": metrics}


@router.post("/workers/heartbeat")
@router.post("/api/v1/workers/heartbeat")
async def process_worker_heartbeat(req: WorkerHeartbeatInput) -> Dict[str, Any]:
    """Records heartbeat signal from a worker node to maintain ONLINE status."""
    success = global_node_manager.update_node_heartbeat(req.node_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Worker node '{req.node_id}' not found.")
    
    nodes = global_node_manager.list_nodes()
    hb_report = global_heartbeat_monitor.check_node_heartbeats(nodes)
    return {"status": "success", "heartbeat_acknowledged": True, "node_id": req.node_id, "cluster_heartbeat_report": hb_report}


@router.get("/distributed/dashboard")
@router.get("/api/v1/distributed/dashboard")
async def get_distributed_dashboard() -> Dict[str, Any]:
    """Retrieves Distributed System Dashboard data: Active Worker Nodes, Queue Status, Running Tasks, Cluster Health, Resource Utilization, Average Task Time, Failed Jobs, Auto-Scaling Status."""
    metrics = global_cluster_monitoring_service.get_cluster_metrics()
    nodes = global_node_manager.list_nodes()
    tasks = global_distributed_task_queue.get_queue_status()
    cloud_profiles = global_node_manager.get_cloud_deployment_profiles()

    return {
        "status": "success",
        "distributed_dashboard": {
            "metrics": metrics,
            "active_worker_nodes": nodes,
            "queued_tasks": tasks,
            "cloud_deployment_profiles": cloud_profiles
        }
    }
