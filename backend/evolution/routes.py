"""
AIForge Day 24 — Autonomous Software Evolution REST API Routes
===============================================================
Endpoints for:
- GET  /api/projects/{projectId}/evolution/analyze
- GET  /api/projects/{projectId}/evolution/debt
- GET  /api/projects/{projectId}/evolution/roadmap
- POST /api/projects/{projectId}/evolution/recommendations/{recId}/implement
- GET  /api/projects/{projectId}/evolution/history
- POST /api/projects/{projectId}/evolution/goal
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user
from backend.evolution.service import global_evolution_service

day24_evolution_router = APIRouter(prefix="/api/projects", tags=["Autonomous Software Evolution Engine"])


class SetGoalPayload(BaseModel):
    goal: str = "Enterprise Deployment"


class ImplementRecPayload(BaseModel):
    simulate_failure: bool = False


@day24_evolution_router.get("/{project_id}/evolution/analyze")
async def analyze_project_evolution(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    res = global_evolution_service.analyze_project(project_id)
    return {"status": "success", "analysis": res.model_dump()}


@day24_evolution_router.get("/{project_id}/evolution/debt")
async def get_technical_debt(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    res = global_evolution_service.analyze_project(project_id)
    return {
        "status": "success",
        "debt_score": res.debt_score.model_dump(),
        "debt_items": [i.model_dump() for i in res.debt_items]
    }


@day24_evolution_router.get("/{project_id}/evolution/roadmap")
async def get_evolution_roadmap(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    res = global_evolution_service.analyze_project(project_id)
    return {"status": "success", "roadmap": res.roadmap.model_dump()}


@day24_evolution_router.post("/{project_id}/evolution/recommendations/{rec_id}/implement")
async def implement_recommendation(
    project_id: str,
    rec_id: str,
    payload: Optional[ImplementRecPayload] = None,
    user: dict = Depends(get_current_user)
):
    sim_fail = payload.simulate_failure if payload else False
    res = global_evolution_service.implement_recommendation(project_id, rec_id, sim_fail)
    return {"status": "success", "result": res}


@day24_evolution_router.get("/{project_id}/evolution/history")
async def get_evolution_history(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    hist = global_evolution_service.get_history(project_id)
    return {"status": "success", "history": [h.model_dump() for h in hist]}


@day24_evolution_router.post("/{project_id}/evolution/goal")
async def set_evolution_goal(
    project_id: str,
    payload: SetGoalPayload,
    user: dict = Depends(get_current_user)
):
    global_evolution_service.set_user_goal(project_id, payload.goal)
    return {"status": "success", "goal": payload.goal}
