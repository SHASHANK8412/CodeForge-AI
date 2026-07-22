import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from backend.monitoring.monitor import OpsMonitor
from backend.monitoring.scheduler import OpsScheduler
from backend.monitoring.config import sre_settings

_logger = logging.getLogger("aiforge.sre")

# Global SRE instance shared between scheduler and REST endpoints
global_monitor = OpsMonitor()
global_scheduler = OpsScheduler(global_monitor)

router = APIRouter(prefix="/dashboard/monitoring", tags=["monitoring"])

@router.get("/status")
async def get_system_status():
    """
    Returns overall system health indicators: health score, active incidents, MTTR, MTBF, and SLA rates.
    """
    history_records = global_monitor.knowledge_base.get_records()
    metrics = global_monitor.analytics.calculate_metrics(
        history_records=history_records,
        scaling_events_count=len(global_monitor.scaling_events)
    )
    
    return {
        "success": True,
        "health_score": global_monitor.latest_health_check.get("health_score", 100),
        "uptime_compliance_pct": metrics.get("sla_compliance_pct", 100.0),
        "active_incidents_count": len(global_monitor.active_incidents),
        "mttr_seconds": metrics.get("mttr_seconds", 0.0),
        "mtbf_hours": metrics.get("mtbf_hours", 168.0),
        "active_replicas": global_monitor.autoscaler.backend_replicas,
        "memory_limit_mb": global_monitor.autoscaler.backend_memory_limit_mb,
    }

@router.get("/metrics")
def get_current_metrics():
    """
    Returns latest collected CPU, Memory, Disk, and API throughput metrics.
    """
    return {
        "success": True,
        "telemetry": global_monitor.latest_metrics or global_monitor.metrics_collector.collect_metrics()
    }

@router.get("/history")
def get_metrics_history():
    """
    Returns historical telemetry ring buffer logs for charting.
    """
    return {
        "success": True,
        "history": global_monitor.metrics_collector.get_history()
    }

@router.get("/incidents")
def get_incidents_log(status: str | None = None):
    """
    Returns active or historical incidents logs.
    """
    records = global_monitor.knowledge_base.get_records()
    if status == "active":
        return {
            "success": True,
            "incidents": [i.model_dump() for i in global_monitor.active_incidents]
        }
    return {
        "success": True,
        "incidents": records
    }

@router.get("/scaling-events")
def get_scaling_events():
    """
    Returns history log of horizontal and vertical scaling actions.
    """
    return {
        "success": True,
        "replicas": global_monitor.autoscaler.backend_replicas,
        "events": global_monitor.scaling_events
    }

@router.post("/simulate-failure")
async def simulate_failure(signature: str = Query(..., description="Signature of failure to inject: e.g. db_connection_failure, high_cpu, ollama_failure")):
    """
    Mocks a threshold violation or service outage to trigger and verify autonomous SRE self-healing.
    """
    _logger.warning(f"[SRE SIMULATION] Injecting failure scenario signature: {signature}")
    
    # 1. Setup mock failure triggers in collector/healthcheck
    if signature == "db_connection_failure":
        # Force database check to return Unhealthy
        async def mock_db_check():
            return {"status": "Unhealthy", "error": "Postgres connection pool exhausted."}
        global_monitor.health_checker.check_database = mock_db_check
        
    elif signature == "high_cpu":
        # Force metrics CPU parameter to cross limit
        def mock_cpu_metrics():
            m = global_monitor.metrics_collector.app_metrics.copy()
            # return custom CPU
            snapshot = global_monitor.metrics_collector.collect_metrics()
            snapshot["infrastructure"]["cpu_utilization"] = 92.5
            global_monitor.metrics_collector.history.append(snapshot)
            return snapshot
        global_monitor.metrics_collector.collect_metrics = mock_cpu_metrics

    elif signature == "ollama_failure":
        async def mock_ollama_check():
            return {"status": "Unhealthy", "error": "Model connection refused."}
        global_monitor.health_checker.check_ollama = mock_ollama_check
        
    else:
        raise HTTPException(status_code=400, detail=f"Simulation scenario '{signature}' not supported.")

    # 2. Force SRE loop step to run immediately
    outcome = await global_monitor.execute_operations_step()
    return {
        "success": True,
        "message": f"Failure scenario '{signature}' successfully simulated.",
        "sre_outcome": {
            "health_score": outcome.get("health_score"),
            "active_incidents": outcome.get("active_incidents"),
            "recovery_summary": outcome.get("recovery_summary")
        }
    }

@router.get("/export-analytics")
def export_analytics_report(format: str = Query("json", pattern="^(json|csv)$")):
    """
    Exports structured SRE performance metrics as JSON file or CSV data.
    """
    records = global_monitor.knowledge_base.get_records()
    metrics = global_monitor.analytics.calculate_metrics(
        history_records=records,
        scaling_events_count=len(global_monitor.scaling_events)
    )

    if format == "csv":
        csv_data = global_monitor.analytics.export_report_csv(metrics)
        return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=sre_analytics_report.csv"})
    
    return {
        "success": True,
        "analytics": metrics
    }
