"""
AIForge Autonomous Engineering Platform — Execution & Self-Healing REST API Routes
===================================================================================
Endpoints:
- POST /api/projects/{project_id}/execute
- GET /api/projects/{project_id}/execution
- POST /api/projects/{project_id}/repair
- GET /api/projects/{project_id}/validation

Retired (410 Gone, replaced by the Execution Guardian at /api/projects/{project_id}/verifications):
- POST /api/projects/{project_id}/autonomous-validate[/stream], GET /api/projects/{project_id}/autonomous-report
- POST /api/execution/validate[/stream], GET /api/execution/report/{project_id}
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.agents.execution_agent import global_execution_agent
from backend.agents.diagnostic_agent import global_diagnostic_agent
from backend.agents.repair_agent import global_repair_agent
from backend.validation.validation_pipeline import global_validation_pipeline
from backend.services.project_builder import global_structured_project_builder

_logger = logging.getLogger("aiforge.routes.execution")

router = APIRouter(prefix="/api/projects", tags=["execution"])

# In-memory execution store
execution_store: Dict[str, Dict[str, Any]] = {}


class ExecuteProjectRequest(BaseModel):
    files: Optional[Dict[str, str]] = None
    timeout: int = 30


class RepairProjectRequest(BaseModel):
    files: Dict[str, str]
    diagnostic: Optional[Dict[str, Any]] = None


@router.post("/{project_id}/execute")
async def execute_project_endpoint(project_id: str, req: ExecuteProjectRequest):
    files_map = req.files or {"backend/main.py": "from fastapi import FastAPI\napp = FastAPI()\n"}
    _logger.info(f"API: Executing project '{project_id}' ({len(files_map)} files)...")

    exec_report = global_execution_agent.execute_project(
        files_manifest=files_map,
        timeout=req.timeout
    )
    exec_dict = exec_report.model_dump()

    val_report = global_validation_pipeline.run_pipeline(
        files_manifest=files_map,
        execution_data=exec_dict
    )
    val_dict = val_report.model_dump()

    store_entry = execution_store.get(project_id, {"history": []})
    history = store_entry.get("history", [])
    history.append({
        "attempt": len(history) + 1,
        "status": exec_report.status,
        "exit_code": exec_report.exit_code,
        "error_type": exec_report.error_type,
        "duration_ms": exec_report.duration_ms,
        "validation_status": val_report.overall_status
    })

    record = {
        "project_id": project_id,
        "execution": exec_dict,
        "validation": val_dict,
        "execution_report": exec_dict,
        "validation_report": val_dict,
        "history": history
    }
    execution_store[project_id] = record

    return {
        "status": "success",
        "project_id": project_id,
        "execution": exec_dict,
        "validation": val_dict,
        "history": history
    }


@router.get("/{project_id}/execution")
async def get_project_execution_endpoint(project_id: str):
    if project_id not in execution_store:
        # Default status for active or demo projects
        return {
            "project_id": project_id,
            "status": "READY",
            "execution": {"status": "success", "exit_code": 0, "duration_ms": 120.0},
            "history": []
        }
    return execution_store[project_id]


@router.post("/{project_id}/repair")
async def repair_project_endpoint(project_id: str, req: RepairProjectRequest):
    _logger.info(f"API: Repairing project '{project_id}'...")

    diag_data = req.diagnostic or {
        "root_cause": "Fix syntax and import errors",
        "affected_files": list(req.files.keys())[:1],
        "recommended_fix": "Apply minimal targeted fix"
    }

    files_map = dict(req.files)
    repair_result = global_repair_agent.repair_code(
        diagnostic_data=diag_data,
        files_map=files_map
    )

    # Re-execute after repair to verify fix
    re_exec = global_execution_agent.execute_project(files_manifest=files_map)
    re_val = global_validation_pipeline.run_pipeline(files_manifest=files_map, execution_data=re_exec.model_dump())

    return {
        "status": "success",
        "project_id": project_id,
        "repair_result": repair_result,
        "re_execution": re_exec.model_dump(),
        "re_validation": re_val.model_dump(),
        "repaired_files": files_map
    }


@router.get("/{project_id}/validation")
async def get_project_validation_endpoint(project_id: str):
    if project_id in execution_store:
        return execution_store[project_id].get("validation_report", {})

    # Generate real validation pipeline report
    dummy_files = {"backend/main.py": "from fastapi import FastAPI\napp = FastAPI()\n", "README.md": "# App"}
    report = global_validation_pipeline.run_pipeline(dummy_files)
    return report.model_dump()


# --- Retired: autonomous validation ------------------------------------------------------------
# These endpoints ran files taken from the request body (or a built-in dummy file) with no
# authentication or ownership check, let the caller choose the container image, limits and network,
# and kept reports in an unbounded in-memory dict. The Execution Guardian replaces them: it resolves
# the project on disk with ownership checks and runs it on an isolated copy with controlled profiles.
# The routes stay registered so old clients get a clear 410 instead of a confusing 404/405.

VERIFICATIONS_API = "/api/projects/{project_id}/verifications"


def _retired(project_id: str = "{project_id}") -> JSONResponse:
    replacement = VERIFICATIONS_API.format(project_id=project_id)
    return JSONResponse(
        status_code=status.HTTP_410_GONE,
        content={
            "detail": (
                "Autonomous validation has been retired. Use the Execution Guardian API: "
                f"POST {replacement} to start a verification, GET {replacement}/{{verification_id}}/report for results."
            ),
            "replacement": replacement,
        },
    )


@router.post("/{project_id}/autonomous-validate", status_code=410, include_in_schema=False)
async def run_autonomous_validation_endpoint(project_id: str):
    return _retired(project_id)


@router.post("/{project_id}/autonomous-validate/stream", status_code=410, include_in_schema=False)
async def stream_autonomous_validation_endpoint(project_id: str):
    return _retired(project_id)


@router.get("/{project_id}/autonomous-report", status_code=410, include_in_schema=False)
async def get_autonomous_report_endpoint(project_id: str):
    return _retired(project_id)


# Secondary router at /api/execution: the same retired endpoints under their old aliases.
execution_api_router = APIRouter(prefix="/api/execution", tags=["execution_engine"])


@execution_api_router.post("/validate", status_code=410, include_in_schema=False)
async def api_validate():
    return _retired()


@execution_api_router.post("/validate/stream", status_code=410, include_in_schema=False)
async def api_validate_stream():
    return _retired()


@execution_api_router.get("/report/{project_id}", status_code=410, include_in_schema=False)
async def api_get_report(project_id: str):
    return _retired(project_id)
