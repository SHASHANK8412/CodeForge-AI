"""
AIForge Autonomous Engineering Platform — Retired Execution & Self-Healing REST API Routes
==========================================================================================
Every endpoint here is retired and answers 410 Gone, naming the Execution Guardian
(/api/projects/{project_id}/verifications) as the replacement:
- POST /api/projects/{project_id}/execute, GET /api/projects/{project_id}/execution
- POST /api/projects/{project_id}/repair, GET /api/projects/{project_id}/validation
- POST /api/projects/{project_id}/autonomous-validate[/stream], GET /api/projects/{project_id}/autonomous-report
- POST /api/execution/validate[/stream], GET /api/execution/report/{project_id}
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/projects", tags=["execution"])

# These endpoints ran files taken from the request body (or a built-in dummy file) with no
# authentication or ownership check, and kept results in an unbounded in-memory dict. The execute and
# repair endpoints ran the detected build/test command in the server's own working directory, with a
# caller-chosen timeout; the GET endpoints returned made-up defaults or a report on the dummy file.
# The Execution Guardian replaces them: it resolves the project on disk with ownership checks and runs
# it on an isolated copy with controlled profiles.
# The routes stay registered so old clients get a clear 410 instead of a confusing 404/405.

VERIFICATIONS_API = "/api/projects/{project_id}/verifications"


def _retired(project_id: str = "{project_id}", feature: str = "Autonomous validation") -> JSONResponse:
    replacement = VERIFICATIONS_API.format(project_id=project_id)
    return JSONResponse(
        status_code=status.HTTP_410_GONE,
        content={
            "detail": (
                f"{feature} has been retired. Use the Execution Guardian API: "
                f"POST {replacement} to start a verification, GET {replacement}/{{verification_id}}/report for results."
            ),
            "replacement": replacement,
        },
    )


# --- Retired: request-body execution and self-healing -------------------------------------------

_EXECUTION = "Request-body execution and repair"


@router.post("/{project_id}/execute", status_code=410, include_in_schema=False)
async def execute_project_endpoint(project_id: str):
    return _retired(project_id, _EXECUTION)


@router.get("/{project_id}/execution", status_code=410, include_in_schema=False)
async def get_project_execution_endpoint(project_id: str):
    return _retired(project_id, _EXECUTION)


@router.post("/{project_id}/repair", status_code=410, include_in_schema=False)
async def repair_project_endpoint(project_id: str):
    return _retired(project_id, _EXECUTION)


@router.get("/{project_id}/validation", status_code=410, include_in_schema=False)
async def get_project_validation_endpoint(project_id: str):
    return _retired(project_id, _EXECUTION)


# --- Retired: autonomous validation ------------------------------------------------------------

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
