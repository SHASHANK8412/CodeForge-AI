"""
AIForge Autonomous CI/CD Pipeline API Routes
============================================
Endpoints:
- POST /api/projects/{project_id}/ci/run
- GET  /api/projects/{project_id}/ci/history
- GET  /api/projects/{project_id}/ci/runs/{run_id}
- GET  /api/projects/{project_id}/ci/workflow
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.ci.models import CIConfig, CIPipelineResult
from backend.ci.pipeline import global_ci_pipeline_engine
from backend.ci.history_store import global_ci_history_store
from backend.ci.github_actions_generator import global_github_actions_generator

_logger = logging.getLogger("aiforge.routes.ci")

router = APIRouter(prefix="/api/projects", tags=["autonomous_ci"])


class RunCIPipelineRequest(BaseModel):
    files: Optional[Dict[str, str]] = None
    commit_version: str = "main"
    max_repair_attempts: int = 3
    timeout_seconds: float = 30.0
    execution_backend: str = "local"
    docker_enabled: bool = False
    memory_limit: str = "512m"
    cpu_limit: float = 1.0
    network_mode: str = "none"
    generate_github_workflow: bool = True


@router.post("/{project_id}/ci/run")
async def run_ci_pipeline_endpoint(project_id: str, req: RunCIPipelineRequest):
    """
    Executes the full Autonomous CI/CD pipeline on project files.
    """
    files_map = req.files or {
        "backend/main.py": "def get_status(): return {'status': 'OK'}\n",
        "tests/test_main.py": "from backend.main import get_status\ndef test_status(): assert get_status()['status'] == 'OK'\n",
        "requirements.txt": "pytest\n"
    }

    config = CIConfig(
        max_repair_attempts=req.max_repair_attempts,
        timeout_seconds=req.timeout_seconds,
        execution_backend=req.execution_backend,
        docker_enabled=req.docker_enabled or (req.execution_backend == "docker"),
        memory_limit=req.memory_limit,
        cpu_limit=req.cpu_limit,
        network_mode=req.network_mode,
        generate_github_workflow=req.generate_github_workflow
    )

    result = global_ci_pipeline_engine.execute_pipeline(
        files_manifest=files_map,
        project_id=project_id,
        commit_version=req.commit_version,
        config=config
    )

    return {
        "status": "success",
        "project_id": project_id,
        "result": result.model_dump()
    }


@router.get("/{project_id}/ci/history")
async def get_ci_history_endpoint(project_id: str):
    """
    Returns the list of historical CI runs for the project.
    """
    history = global_ci_history_store.get_history(project_id)
    return {
        "project_id": project_id,
        "history": [item.model_dump() for item in history]
    }


@router.get("/{project_id}/ci/runs/{run_id}")
async def get_ci_run_details_endpoint(project_id: str, run_id: str):
    """
    Returns full details for a specific historical CI run.
    """
    run = global_ci_history_store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"CI run '{run_id}' not found.")
    return {
        "project_id": project_id,
        "run": run.model_dump()
    }


@router.get("/{project_id}/ci/workflow")
async def get_github_workflow_endpoint(project_id: str):
    """
    Generates and returns the tailored .github/workflows/aiforge-ci.yml workflow.
    """
    # Sample default files if no prior run
    files = {"backend/main.py": "def main(): pass", "requirements.txt": "pytest"}
    workflow = global_github_actions_generator.generate_workflow(files, project_name=project_id)
    return {
        "project_id": project_id,
        "workflow": workflow
    }


# Secondary router mounted at /api/ci for direct service access
ci_direct_router = APIRouter(prefix="/api/ci", tags=["ci_direct"])


@ci_direct_router.post("/run")
async def direct_ci_run(req: RunCIPipelineRequest, project_id: str = "default_project"):
    return await run_ci_pipeline_endpoint(project_id, req)


@ci_direct_router.get("/history/{project_id}")
async def direct_ci_history(project_id: str):
    return await get_ci_history_endpoint(project_id)


@ci_direct_router.get("/runs/{run_id}")
async def direct_ci_run_details(run_id: str, project_id: str = "default_project"):
    return await get_ci_run_details_endpoint(project_id, run_id)
