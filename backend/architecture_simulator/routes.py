"""
AIForge Day 25 — AI Software Architect Simulator REST API Routes
================================================================
Endpoints for:
- GET  /api/projects/{projectId}/architect/current
- POST /api/projects/{projectId}/architect/simulate
- POST /api/projects/{projectId}/architect/failure
- POST /api/projects/{projectId}/architect/debate
- POST /api/projects/{projectId}/architect/approve
- GET  /api/projects/{projectId}/architect/history
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user
from backend.architecture_simulator.service import global_architecture_simulator_service

day25_architect_router = APIRouter(prefix="/api/projects", tags=["AI Software Architect Simulator"])


class SimulatePayload(BaseModel):
    prompt: str = "Should we add Redis?"


class FailurePayload(BaseModel):
    component_name: str = "PostgreSQL"


class DebatePayload(BaseModel):
    topic: str = "Should we introduce Redis caching?"


@day25_architect_router.get("/{project_id}/architect/current")
async def get_current_architecture(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    diagram = global_architecture_simulator_service.get_current_architecture(project_id)
    return {"status": "success", "architecture": diagram.model_dump()}


@day25_architect_router.post("/{project_id}/architect/simulate")
async def simulate_architecture_scenario(
    project_id: str,
    payload: SimulatePayload,
    user: dict = Depends(get_current_user)
):
    scen, assessment, comparison = global_architecture_simulator_service.simulate_scenario(project_id, payload.prompt)
    return {
        "status": "success",
        "scenario": scen.model_dump(),
        "assessment": assessment.model_dump(),
        "comparison": comparison.model_dump()
    }


@day25_architect_router.post("/{project_id}/architect/failure")
async def simulate_component_failure(
    project_id: str,
    payload: FailurePayload,
    user: dict = Depends(get_current_user)
):
    report = global_architecture_simulator_service.simulate_failure(project_id, payload.component_name)
    return {"status": "success", "failure_report": report.model_dump()}


@day25_architect_router.post("/{project_id}/architect/debate")
async def run_architecture_debate(
    project_id: str,
    payload: DebatePayload,
    user: dict = Depends(get_current_user)
):
    res = global_architecture_simulator_service.run_multi_agent_debate_on_scenario(project_id, payload.topic)
    return {"status": "success", "debate_result": res}


@day25_architect_router.post("/{project_id}/architect/approve")
async def approve_architecture_and_create_plan(
    project_id: str,
    scenario_id: str = Query(...),
    user: dict = Depends(get_current_user)
):
    adr, plan = global_architecture_simulator_service.approve_scenario_and_create_plan(project_id, scenario_id)
    return {"status": "success", "adr": adr.model_dump(), "plan": plan}


@day25_architect_router.get("/{project_id}/architect/history")
async def get_architecture_history(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    hist = global_architecture_simulator_service.get_history(project_id)
    return {"status": "success", "history": [h.model_dump() for h in hist]}
