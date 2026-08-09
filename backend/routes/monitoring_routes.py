"""
FastAPI Routes for Day 46 Enterprise Observability, Monitoring & Autonomous Operations
========================================================================================
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from backend.monitoring.tracing import global_distributed_tracing
from backend.monitoring.metrics import global_metrics_collector
from backend.monitoring.health import global_health_checker
from backend.monitoring.alerts import global_alert_engine
from backend.monitoring.dashboard import global_operations_dashboard
from backend.analytics.trends import global_historical_analytics

router = APIRouter(tags=["Enterprise Observability & Monitoring"])


class RecoveryRequest(BaseModel):
    alert_type: str


@router.get("/api/v1/monitoring/traces")
@router.get("/monitoring/traces")
async def list_traces(trace_id: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Retrieves distributed OpenTelemetry traces and span execution times."""
    if trace_id:
        trace = global_distributed_tracing.get_trace(trace_id)
        return {"status": "success", "trace_id": trace_id, "trace": trace}
    return {"status": "success", "total_traces": len(global_distributed_tracing.traces), "traces": global_distributed_tracing.traces}


@router.get("/api/v1/monitoring/metrics")
@router.get("/monitoring/metrics")
async def get_system_metrics() -> Dict[str, Any]:
    """Retrieves real-time infrastructure, GPU, memory, and LLM metrics."""
    metrics = global_metrics_collector.collect_system_metrics()
    return {"status": "success", "metrics": metrics}


@router.get("/api/v1/monitoring/alerts")
@router.get("/monitoring/alerts")
async def get_active_alerts() -> Dict[str, Any]:
    """Retrieves active system alert conditions."""
    metrics = global_metrics_collector.collect_system_metrics()
    alerts = global_alert_engine.evaluate_system_alerts(metrics)
    return {"status": "success", "active_alerts_count": len(alerts), "alerts": alerts}


@router.post("/api/v1/monitoring/recover")
@router.post("/monitoring/recover")
async def trigger_autonomous_recovery(req: RecoveryRequest) -> Dict[str, Any]:
    """Triggers autonomous recovery action for an alert threshold."""
    res = global_alert_engine.trigger_autonomous_recovery(req.alert_type)
    return {"status": "success", "recovery": res}


@router.get("/api/v1/monitoring/dashboard")
@router.get("/monitoring/dashboard")
async def get_operations_dashboard() -> Dict[str, Any]:
    """Retrieves real-time AI Operations Dashboard status payload."""
    dash = global_operations_dashboard.get_operations_dashboard()
    return {"status": "success", "operations_dashboard": dash}


@router.get("/api/v1/analytics/trends")
@router.get("/analytics/trends")
async def get_trend_analytics() -> Dict[str, Any]:
    """Retrieves long-term historical analytics and trend reports."""
    trends = global_historical_analytics.get_trend_reports()
    return {"status": "success", "trends": trends}
