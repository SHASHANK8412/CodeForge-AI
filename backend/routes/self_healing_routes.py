"""
FastAPI Routes for Day 42 Autonomous Error Detection, Root Cause Analysis & Self-Healing Pipeline
===================================================================================================
Exposes REST APIs for error monitoring, root cause analysis, self-healing pipeline execution, error history logs, metrics, and timeline state.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List, Union

from backend.self_healing.error_monitor import global_error_monitor
from backend.self_healing.root_cause import global_root_cause_analyzer
from backend.self_healing.fix_generator import global_fix_generator
from backend.self_healing.learning_store import global_learning_store
from backend.self_healing.retry_manager import global_retry_manager
from backend.services.retry_manager import global_retry_manager_service
from backend.agents.error_analyzer import global_error_analyzer
from backend.agents.root_cause import global_root_cause_finder
from backend.agents.self_healing import global_self_healing_agent

router = APIRouter(tags=["Autonomous Error Detection & Self-Healing Pipeline"])


class TriggerFixInput(BaseModel):
    error_id: str


class TriggerRetryInput(BaseModel):
    error_id: str
    error_type: Optional[str] = "Database"
    message: Optional[str] = "Connection timeout"
    file: Optional[str] = "database.py"


class PipelineInput(BaseModel):
    error_log: Union[str, Dict[str, Any]]
    project_id: Optional[str] = "default_project"


@router.get("/errors")
@router.get("/failures")
@router.get("/api/v1/errors")
@router.get("/api/v1/failures")
async def list_monitored_errors(
    error_type: Optional[str] = Query(None, description="Filter by error type"),
    status: Optional[str] = Query(None, description="Filter by status")
) -> Dict[str, Any]:
    """Retrieves monitored system failures."""
    errors = global_error_monitor.get_errors(error_type=error_type, status=status)
    return {"status": "success", "total_errors": len(errors), "errors": errors}


@router.post("/fix")
@router.post("/api/v1/fix")
async def generate_and_apply_patch(req: TriggerFixInput) -> Dict[str, Any]:
    """Triggers Root Cause Analysis and generates an automated code fix patch."""
    errors = global_error_monitor.get_errors()
    matching = [e for e in errors if e["error_id"] == req.error_id]
    if not matching:
        raise HTTPException(status_code=404, detail=f"Error ID '{req.error_id}' not found.")

    err_report = matching[0]
    rca = global_root_cause_analyzer.analyze(err_report)
    fix = global_fix_generator.generate_and_apply_fix(rca)
    global_error_monitor.update_error_status(req.error_id, "RESOLVED")

    return {
        "status": "success",
        "rca_analysis": rca,
        "fix_patch": fix
    }


@router.get("/learning")
@router.get("/api/v1/learning")
async def get_learning_store_lessons(q: Optional[str] = Query(None, description="Search query")) -> Dict[str, Any]:
    """Retrieves reusable failure lessons and proven solutions."""
    if q:
        lessons = global_learning_store.search_lessons(q)
    else:
        lessons = global_learning_store.get_all_lessons()
    return {"status": "success", "total_lessons": len(lessons), "lessons": lessons}


@router.post("/retry")
@router.post("/api/v1/retry")
async def retry_self_healing_attempt(req: TriggerRetryInput) -> Dict[str, Any]:
    """Executes self-healing retry attempt."""
    err_report = {
        "error_id": req.error_id,
        "error_type": req.error_type or "Database",
        "message": req.message or "Connection timeout",
        "file": req.file or "database.py"
    }
    result = global_retry_manager.execute_self_healing_attempt(err_report)
    return {"status": "success", "retry_attempt_result": result}


@router.get("/self_healing/dashboard")
@router.get("/api/v1/self_healing/dashboard")
async def get_self_healing_dashboard() -> Dict[str, Any]:
    """Retrieves Self-Healing Dashboard metrics."""
    dash = global_retry_manager.get_self_healing_dashboard()
    return {"status": "success", "self_healing_dashboard": dash}


# --- Day 42 Pipeline REST APIs ---

@router.post("/api/v1/self-healing/pipeline")
@router.post("/self-healing/pipeline")
async def run_pipeline(req: PipelineInput) -> Dict[str, Any]:
    """
    Executes Day 42 Error Detection, Root Cause Analysis, Self-Healing, and Retry Loop (up to 3 retries).
    """
    result = global_retry_manager_service.run_self_healing_pipeline(
        error_log=req.error_log,
        project_id=req.project_id or "default_project"
    )
    return {"status": "success", "pipeline_result": result}


@router.get("/api/v1/self-healing/metrics")
@router.get("/self-healing/metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Retrieves Dashboard Metrics: Errors Found, Errors Fixed, Retries Used, Average Confidence, Build Success %.
    """
    metrics = global_retry_manager_service.get_dashboard_metrics()
    return {"status": "success", "metrics": metrics}


@router.get("/api/v1/self-healing/timeline/{project_id}")
@router.get("/self-healing/timeline/{project_id}")
async def get_timeline(project_id: str) -> Dict[str, Any]:
    """
    Retrieves UI Timeline progress (Planning, Architecture, Frontend, Backend, Testing, Debugging) and current error/fix status.
    """
    timeline_data = global_retry_manager_service.get_timeline_status(project_id)
    return {"status": "success", "timeline_data": timeline_data}


@router.get("/api/v1/self-healing/history")
@router.get("/self-healing/history")
async def get_error_history() -> Dict[str, Any]:
    """
    Retrieves persistent error log history from backend/logs/error_history.json.
    """
    history = global_retry_manager_service.load_history()
    return {"status": "success", "total_records": len(history), "history": history}
