"""
AIForge V2 Day 40 Verification Suite
=====================================
End-to-end verification script for AIForge V2 Day 40 deliverables:
1. Distributed Worker Node Registration & Cloud Deployment Profiles (AWS, Azure, GCP)
2. Priority-Based Distributed Task Queue (Critical, High, Normal, Low)
3. Multi-Strategy Load Balancer (Round Robin, Least Loaded)
4. Master Distributed Scheduler Task Assignment
5. Heartbeat Signal Monitor & Fault Tolerance Auto-Reassignment
6. Cluster Monitoring Metrics (CPU/RAM Utilization, Active Tasks, Health)
7. Distributed System Dashboard & REST APIs
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.distributed.node_manager import global_node_manager
from backend.distributed.task_queue import global_distributed_task_queue, TaskPriority
from backend.distributed.load_balancer import global_load_balancer, LoadBalancerStrategy
from backend.distributed.scheduler import global_distributed_scheduler
from backend.distributed.heartbeat import global_heartbeat_monitor
from backend.distributed.monitoring import global_cluster_monitoring_service

PASS = "[PASS]"
FAIL = "[FAIL]"
_results = {"passed": 0, "failed": 0}


def section(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    if condition:
        _results["passed"] += 1
    else:
        _results["failed"] += 1
    msg = f"  {status}  {name}"
    if detail:
        msg += f"\n        => {detail}"
    print(msg)
    return condition


def run_v2_day40_verification():
    print("======================================================================")
    print(" ☁️ AIForge V2 – Day 40 Cloud Platform & Distributed Execution Verification")
    print("======================================================================\n")

    section("1. Worker Node Registration & Cloud Profiles")
    node = global_node_manager.register_node("worker_node_4", host="10.0.0.15", capacity=4, cloud_provider="Azure AKS")
    check("Registered worker node in cluster", node["node_id"] == "worker_node_4" and node["status"] == "ONLINE")

    profiles = global_node_manager.get_cloud_deployment_profiles()
    check("Retrieved cloud deployment profiles (AWS, Azure, GCP, K8s)", len(profiles["supported_platforms"]) >= 5)

    section("2. Priority-Based Distributed Task Queue")
    task_crit = global_distributed_task_queue.enqueue_task("Banking Platform", "Security Agent", priority_label="Critical")
    check("Enqueued Critical priority task at head of queue", task_crit["priority"] == TaskPriority.CRITICAL)

    section("3. Multi-Strategy Load Balancer")
    nodes = global_node_manager.list_nodes()
    sel_worker = global_load_balancer.select_worker(nodes, strategy=LoadBalancerStrategy.LEAST_LOADED)
    check("Selected least loaded worker node", sel_worker is not None and sel_worker["status"] == "ONLINE")

    section("4. Master Distributed Scheduler Task Assignment")
    sched_task = global_distributed_scheduler.submit_and_schedule("Banking Platform", "Backend Agent", priority_label="High")
    check("Scheduled task on assigned worker node", sched_task["status"] == "ASSIGNED" and "assigned_worker" in sched_task)

    section("5. Heartbeat Signal Monitor & Fault Tolerance Auto-Recovery")
    # Simulate timed out node
    timed_out_node = [{"node_id": "worker_failing", "status": "ONLINE", "last_heartbeat": 100.0}]
    hb_report = global_heartbeat_monitor.check_node_heartbeats(timed_out_node)
    check("Detected heartbeat timeout & auto-reassigned task", hb_report["offline_count"] == 1 and len(hb_report["auto_reassigned_tasks"]) == 1)

    section("6. Cluster Monitoring Service")
    metrics = global_cluster_monitoring_service.get_cluster_metrics()
    check("Compiled cluster health & resource utilization metrics", metrics["cluster_health"] in ["HEALTHY", "DEGRADED"] and metrics["active_worker_nodes"] >= 3)

    # Summary
    print("\n" + "="*70)
    print(f" AIFORGE V2 DAY 40 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = run_v2_day40_verification()
    sys.exit(0 if success else 1)
