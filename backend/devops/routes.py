"""
AIForge Day 20 — Autonomous DevOps & Deployment REST API Routes
=================================================================
Endpoints for:
- POST /api/projects/{projectId}/devops/plan
- POST /api/projects/{projectId}/devops/deploy
- GET  /api/projects/{projectId}/devops/status
- GET  /api/projects/{projectId}/devops/history
- GET  /api/projects/{projectId}/devops/compare
- GET  /api/projects/{projectId}/devops/production-health
- POST /api/projects/{projectId}/devops/rollback
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user
from backend.devops.service import global_devops_service

day20_devops_router = APIRouter(prefix="/api/projects", tags=["Autonomous DevOps & Deployment Engine"])


class DeployPayload(BaseModel):
    simulate_health_failure: bool = False
    simulate_smoke_failure: bool = False
    bypass_readiness: bool = False


class RollbackPayload(BaseModel):
    target_version: int = 1


@day20_devops_router.post("/{project_id}/devops/plan")
async def get_deployment_plan(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    plan = global_devops_service.prepare_deployment_plan(project_id)
    return {"status": "success", "plan": plan.model_dump()}


@day20_devops_router.post("/{project_id}/devops/deploy")
async def deploy_project(
    project_id: str,
    payload: Optional[DeployPayload] = None,
    user: dict = Depends(get_current_user)
):
    sim_h = payload.simulate_health_failure if payload else False
    sim_s = payload.simulate_smoke_failure if payload else False
    b_read = payload.bypass_readiness if payload else False

    status_obj = global_devops_service.deploy_project(
        project_id,
        simulate_health_failure=sim_h,
        simulate_smoke_failure=sim_s,
        bypass_readiness=b_read
    )
    return {"status": "success", "deployment": status_obj.model_dump()}


@day20_devops_router.get("/{project_id}/devops/status")
async def get_deployment_status(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    history = global_devops_service.get_deployment_history(project_id)
    latest = history.deployments[-1] if history.deployments else None
    return {"status": "success", "deployment": latest.model_dump() if latest else None}


@day20_devops_router.get("/{project_id}/devops/history")
async def get_deployment_history(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    history = global_devops_service.get_deployment_history(project_id)
    return {"status": "success", "history": history.model_dump()}


@day20_devops_router.get("/{project_id}/devops/compare")
async def compare_deployments(
    project_id: str,
    v1: int = Query(1),
    v2: int = Query(2),
    user: dict = Depends(get_current_user)
):
    comp = global_devops_service.compare_deployments(project_id, v1, v2)
    return {"status": "success", "comparison": comp.model_dump()}


@day20_devops_router.get("/{project_id}/devops/production-health")
async def get_production_health(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    health = global_devops_service.get_production_health(project_id)
    return {"status": "success", "production_health": health.model_dump()}


@day20_devops_router.post("/{project_id}/devops/rollback")
async def rollback_deployment(
    project_id: str,
    payload: Optional[RollbackPayload] = None,
    user: dict = Depends(get_current_user)
):
    t_ver = payload.target_version if payload else 1
    from backend.devops.rollback import global_rollback_engine
    rolled = global_rollback_engine.execute_rollback(project_id, t_ver)
    return {"status": "success", "deployment": rolled.model_dump()}
