"""
AIForge Day 26 — OpenTelemetry Observability REST API Routes
============================================================
Endpoints for:
- GET /api/admin/observability (legacy admin view)
- GET /api/admin/evaluations
- POST /api/feedback
- GET /api/projects/{projectId}/observability/metrics
- GET /api/projects/{projectId}/observability/traces
- GET /api/projects/{projectId}/observability/traces/{traceId}
- GET /api/projects/{projectId}/observability/regression
- GET /api/projects/{projectId}/observability/readiness
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.auth.dependencies import get_current_user
from backend.observability.telemetry import global_observability_telemetry
from backend.observability.evaluator import global_evaluation_engine
from backend.observability.feedback import FeedbackSubmissionRequest, submit_user_feedback, get_project_feedback
from backend.observability.service import global_opentelemetry_service
from backend.observability.integration import global_telemetry_multi_system_bridge
from backend.observability.dna_mapper import global_dna_trace_mapper

router = APIRouter(tags=["Observability, Distributed Tracing & Reliability"])


@router.get("/api/admin/observability")
def get_observability_dashboard_data(current_user: dict = Depends(get_current_user)):
    return global_observability_telemetry.get_dashboard_telemetry()


@router.get("/api/admin/evaluations")
def get_evaluations_center_data(current_user: dict = Depends(get_current_user)):
    return global_evaluation_engine.get_evaluation_data()


@router.post("/api/feedback")
def submit_feedback_endpoint(req: FeedbackSubmissionRequest, current_user: dict = Depends(get_current_user)):
    entry = submit_user_feedback(current_user["id"], req)
    return {"success": True, "feedback": entry}


@router.get("/api/feedback/{project_id}")
def get_project_feedback_endpoint(project_id: str):
    return {"feedback": get_project_feedback(project_id)}


# --- DAY 26 OPENTELEMETRY ENDPOINTS ---

@router.get("/api/projects/{project_id}/observability/metrics")
def get_project_observability_metrics(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    m = global_opentelemetry_service.get_metrics(project_id)
    return {"status": "success", "metrics": m.model_dump()}


@router.get("/api/projects/{project_id}/observability/traces")
def get_project_traces(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    traces = global_opentelemetry_service.get_traces(project_id)
    return {"status": "success", "traces": [t.model_dump() for t in traces]}


@router.get("/api/projects/{project_id}/observability/traces/{trace_id}")
def get_trace_detail(
    project_id: str,
    trace_id: str,
    user: dict = Depends(get_current_user)
):
    t = global_opentelemetry_service.get_trace_details(project_id, trace_id)
    if not t:
        raise HTTPException(status_code=404, detail="Trace not found")
    dna_map = global_dna_trace_mapper.map_trace_to_dna(t)
    return {"status": "success", "trace": t.model_dump(), "dna_map": dna_map}


@router.get("/api/projects/{project_id}/observability/regression")
def get_performance_regression_alert(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    alert = global_opentelemetry_service.detect_performance_regression(project_id)
    return {"status": "success", "regression": alert.model_dump()}


@router.get("/api/projects/{project_id}/observability/readiness")
def get_observability_readiness_status(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    st = global_telemetry_multi_system_bridge.evaluate_observability_readiness(project_id)
    return {"status": "success", "readiness": st.model_dump()}
