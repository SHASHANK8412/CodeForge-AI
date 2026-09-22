"""
AIForge Day 19 — Production Readiness Gate REST API Routes
===========================================================
Endpoints for:
- POST /api/projects/{projectId}/readiness/run
- GET  /api/projects/{projectId}/readiness/report
- POST /api/projects/{projectId}/readiness/approve
- POST /api/projects/{projectId}/readiness/reject
- POST /api/projects/{projectId}/readiness/autofix
- GET  /api/projects/{projectId}/readiness/history
- GET  /api/projects/{projectId}/readiness/diff
- GET  /api/projects/{projectId}/readiness/export
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user
from backend.readiness.service import global_readiness_service

day19_readiness_router = APIRouter(prefix="/api/projects", tags=["Autonomous Production Readiness Gate"])


class ApprovalPayload(BaseModel):
    approver: str = "Chief Architect"


class RunReadinessPayload(BaseModel):
    simulate_security_block: bool = False


@day19_readiness_router.post("/{project_id}/readiness/run")
async def run_readiness_gate(
    project_id: str,
    payload: Optional[RunReadinessPayload] = None,
    user: dict = Depends(get_current_user)
):
    sim_block = payload.simulate_security_block if payload else False
    report = global_readiness_service.run_readiness_check(project_id, simulate_security_block=sim_block)
    return {"status": "success", "report": report.model_dump()}


@day19_readiness_router.get("/{project_id}/readiness/report")
async def get_readiness_report(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    report = global_readiness_service.get_latest_report(project_id)
    return {"status": "success", "report": report.model_dump()}


@day19_readiness_router.post("/{project_id}/readiness/approve")
async def approve_production_deployment(
    project_id: str,
    payload: Optional[ApprovalPayload] = None,
    user: dict = Depends(get_current_user)
):
    approver = payload.approver if payload else "Chief Architect"
    success = global_readiness_service.approve_deployment(project_id, approver)
    return {"status": "success" if success else "blocked", "approved": success}


@day19_readiness_router.post("/{project_id}/readiness/reject")
async def reject_production_deployment(
    project_id: str,
    payload: Optional[ApprovalPayload] = None,
    user: dict = Depends(get_current_user)
):
    approver = payload.approver if payload else "Chief Architect"
    success = global_readiness_service.reject_deployment(project_id, approver)
    return {"status": "success", "rejected": success}


@day19_readiness_router.post("/{project_id}/readiness/autofix")
async def autofix_readiness_blockers(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    report = global_readiness_service.autofix_blocking_issues(project_id)
    return {"status": "success", "report": report.model_dump()}


@day19_readiness_router.get("/{project_id}/readiness/history")
async def get_readiness_history(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    history = global_readiness_service.get_history(project_id)
    return {"status": "success", "history": history.model_dump()}


@day19_readiness_router.get("/{project_id}/readiness/diff")
async def get_readiness_diff(
    project_id: str,
    v1: int = Query(1),
    v2: int = Query(2),
    user: dict = Depends(get_current_user)
):
    diff = global_readiness_service.get_diff(project_id, v1, v2)
    return {"status": "success", "diff": diff.model_dump()}


@day19_readiness_router.get("/{project_id}/readiness/export")
async def export_readiness_report(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    json_str = global_readiness_service.export_report_json(project_id)
    return {"status": "success", "json": json_str}
