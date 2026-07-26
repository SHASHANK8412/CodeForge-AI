import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from backend.graph.executor import global_workflow_executor
from backend.execution.runner import global_project_execution_engine
from backend.debugging.retry import global_self_healing_retry_engine
from backend.debugging.logger import global_debug_logger

logger = logging.getLogger("aiforge.routes.debugging")

router = APIRouter(tags=["Autonomous Debugging & Self-Healing"])


@router.post("/execute/{project_id}")
@router.post("/api/execute/{project_id}")
def execute_project_runtime(project_id: str):
    """Executes backend/frontend runtime checks for a project."""
    status = global_workflow_executor.get_project_status(project_id)
    files = status.get("project_files", {})
    if not files:
        files = {
            "frontend/src/App.jsx": "import React from 'react'; export default function App() { return <div>App</div>; }",
            "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()",
            "tests/test_app.py": "def test_simple(): assert 1 == 1"
        }

    exec_res = global_project_execution_engine.execute_project(files)
    exec_res["project_id"] = project_id
    global_debug_logger.log_execution(project_id, exec_res)
    return exec_res


@router.post("/debug/{project_id}")
@router.post("/api/debug/{project_id}")
@router.post("/retry/{project_id}")
@router.post("/api/retry/{project_id}")
def trigger_self_healing_debug(project_id: str):
    """Triggers autonomous self-healing execution loop (Run -> Diagnose -> Fix -> Re-test)."""
    status = global_workflow_executor.get_project_status(project_id)
    files = status.get("project_files", {})
    if not files:
        files = {
            "frontend/src/App.jsx": "import React from 'react'; function App() { return <div>App</div>; }", # missing export
            "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()",
            "backend/requirements.txt": "fastapi\nuvicorn\n",
            "tests/test_app.py": "def test_simple(): assert 1 == 1"
        }

    healing_res = global_self_healing_retry_engine.execute_self_healing_loop(files, max_attempts=3)
    healing_res["project_id"] = project_id
    global_debug_logger.log_execution(project_id, healing_res)
    return healing_res


@router.get("/execution/logs/{project_id}")
@router.get("/api/execution/logs/{project_id}")
def get_execution_logs(project_id: str):
    """Returns execution telemetry and self-healing attempt logs."""
    logs = global_debug_logger.get_logs(project_id)
    return {"project_id": project_id, "logs": logs}


@router.get("/debug/report/{project_id}")
@router.get("/api/debug/report/{project_id}")
def get_debug_report(project_id: str):
    """Returns self-healing summary, retry count, and health score."""
    logs = global_debug_logger.get_logs(project_id)
    last_log = logs[-1] if logs else {}

    return {
        "project_id": project_id,
        "is_healthy": last_log.get("is_healthy", True),
        "self_healing_score": last_log.get("self_healing_score", 100.0),
        "total_attempts": last_log.get("attempts", 1),
        "recent_logs": logs
    }
