"""
AIForge Production Readiness REST API (evidence only; see backend/readiness/checks.py)
=====================================================================================
- POST /api/projects/{projectId}/readiness/run       evaluate the current evidence
- GET  /api/projects/{projectId}/readiness/report    latest evaluation (evaluates once if there is none)
- POST /api/projects/{projectId}/readiness/approve   record approval; refused when BLOCKED or INCOMPLETE
- POST /api/projects/{projectId}/readiness/reject
- GET  /api/projects/{projectId}/readiness/history   real evaluations only
- GET  /api/projects/{projectId}/readiness/diff      between two evaluated versions (404 otherwise)
- GET  /api/projects/{projectId}/readiness/export
Project access is checked as for Autopilot. Readiness does not fix or deploy anything.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user
from backend.evolution.routes import _project_dir
from backend.readiness.service import global_readiness_service

day19_readiness_router = APIRouter(prefix="/api/projects", tags=["Production Readiness"])


class ApprovalPayload(BaseModel):
    approver: str = "Chief Architect"


@day19_readiness_router.post("/{project_id}/readiness/run")
async def run_readiness_gate(project_id: str, user: dict = Depends(get_current_user)):
    path = _project_dir(project_id, user)
    report = global_readiness_service.run_readiness_check(project_id, project=path)
    return {"status": "success", "report": report.model_dump()}


@day19_readiness_router.get("/{project_id}/readiness/report")
async def get_readiness_report(project_id: str, user: dict = Depends(get_current_user)):
    _project_dir(project_id, user)
    report = global_readiness_service.get_latest_report(project_id)
    return {"status": "success", "report": report.model_dump()}


@day19_readiness_router.post("/{project_id}/readiness/approve")
async def approve_production_deployment(project_id: str, payload: Optional[ApprovalPayload] = None,
                                        user: dict = Depends(get_current_user)):
    _project_dir(project_id, user)
    approver = payload.approver if payload else "Chief Architect"
    success = global_readiness_service.approve_deployment(project_id, approver)
    return {"status": "success" if success else "refused", "approved": success}


@day19_readiness_router.post("/{project_id}/readiness/reject")
async def reject_production_deployment(project_id: str, payload: Optional[ApprovalPayload] = None,
                                       user: dict = Depends(get_current_user)):
    _project_dir(project_id, user)
    approver = payload.approver if payload else "Chief Architect"
    success = global_readiness_service.reject_deployment(project_id, approver)
    return {"status": "success", "rejected": success}


@day19_readiness_router.get("/{project_id}/readiness/history")
async def get_readiness_history(project_id: str, user: dict = Depends(get_current_user)):
    _project_dir(project_id, user)
    history = global_readiness_service.get_history(project_id)
    return {"status": "success", "history": history.model_dump()}


@day19_readiness_router.get("/{project_id}/readiness/diff")
async def get_readiness_diff(project_id: str, v1: int = Query(1), v2: int = Query(2), user: dict = Depends(get_current_user)):
    _project_dir(project_id, user)
    try:
        diff = global_readiness_service.get_diff(project_id, v1, v2)
    except KeyError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e).strip("'"))
    return {"status": "success", "diff": diff.model_dump()}


@day19_readiness_router.get("/{project_id}/readiness/export")
async def export_readiness_report(project_id: str, user: dict = Depends(get_current_user)):
    _project_dir(project_id, user)
    return {"status": "success", "json": global_readiness_service.export_report_json(project_id)}
