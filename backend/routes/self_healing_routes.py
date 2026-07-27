"""
FastAPI Routes for Day 32 Autonomous Debugging, Self-Healing & Root Cause Analysis
====================================================================================
Exposes REST APIs for error monitoring, root cause analysis, automated fix patch generation, learning store retrieval, retry escalations, and self-healing dashboard.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from backend.self_healing.error_monitor import global_error_monitor
from backend.self_healing.root_cause import global_root_cause_analyzer
from backend.self_healing.fix_generator import global_fix_generator
from backend.self_healing.learning_store import global_learning_store
from backend.self_healing.retry_manager import global_retry_manager

router = APIRouter(tags=["Autonomous Debugging & Self-Healing"])


class TriggerFixInput(BaseModel):
    error_id: str


class TriggerRetryInput(BaseModel):
    error_id: str
    error_type: Optional[str] = "Database"
    message: Optional[str] = "Connection timeout"
    file: Optional[str] = "database.py"


@router.get("/errors")
@router.get("/failures")
@router.get("/api/v1/errors")
@router.get("/api/v1/failures")
async def list_monitored_errors(
    error_type: Optional[str] = Query(None, description="Filter by error type (e.g. Database, API, Test, Build)"),
    status: Optional[str] = Query(None, description="Filter by status (DETECTED, RESOLVED, ESCALATED)")
) -> Dict[str, Any]:
    """Retrieves monitored system failures across 10 pipeline sources."""
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
async def get_learning_store_lessons(q: Optional[str] = Query(None, description="Search query for recurring solutions")) -> Dict[str, Any]:
    """Retrieves reusable failure lessons and proven solutions from the Learning Store."""
    if q:
        lessons = global_learning_store.search_lessons(q)
    else:
        lessons = global_learning_store.get_all_lessons()
    return {"status": "success", "total_lessons": len(lessons), "lessons": lessons}


@router.post("/retry")
@router.post("/api/v1/retry")
async def retry_self_healing_attempt(req: TriggerRetryInput) -> Dict[str, Any]:
    """Executes self-healing retry attempt. Escalates to human review if attempt limit is exceeded."""
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
    """Retrieves Self-Healing Dashboard metrics: Active Errors, Root Causes, Auto Fixes, Retry Counts, Success Rate %."""
    dash = global_retry_manager.get_self_healing_dashboard()
    return {"status": "success", "self_healing_dashboard": dash}
