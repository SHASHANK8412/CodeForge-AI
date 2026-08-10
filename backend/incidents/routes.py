"""
AIForge Day 21 — Autonomous Incident Response REST API Routes
==============================================================
Endpoints for:
- POST /api/projects/{projectId}/incidents/detect
- GET  /api/projects/{projectId}/incidents
- GET  /api/projects/{projectId}/incidents/{incidentId}
- POST /api/projects/{projectId}/incidents/{incidentId}/approve
- POST /api/projects/{projectId}/incidents/{incidentId}/rollback
- GET  /api/projects/{projectId}/incidents/metrics
- POST /api/projects/{projectId}/incidents/chat
- GET  /api/projects/{projectId}/incidents/{incidentId}/report
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user
from backend.incidents.service import global_incident_service

day21_incidents_router = APIRouter(prefix="/api/projects", tags=["Autonomous Incident Response & Self-Healing"])


class TriggerIncidentPayload(BaseModel):
    simulate_db_failure: bool = False
    simulate_perf_failure: bool = False
    simulate_validation_failure: bool = False
    simulate_repeated_loop: bool = False


class IncidentChatPayload(BaseModel):
    question: str = "Why did this incident happen?"


@day21_incidents_router.post("/{project_id}/incidents/detect")
async def trigger_incident_detection(
    project_id: str,
    payload: Optional[TriggerIncidentPayload] = None,
    user: dict = Depends(get_current_user)
):
    sim_db = payload.simulate_db_failure if payload else False
    sim_perf = payload.simulate_perf_failure if payload else False
    sim_val = payload.simulate_validation_failure if payload else False
    sim_loop = payload.simulate_repeated_loop if payload else False

    inc = global_incident_service.trigger_incident_workflow(
        project_id,
        simulate_db_failure=sim_db,
        simulate_perf_failure=sim_perf,
        simulate_validation_failure=sim_val,
        simulate_repeated_loop=sim_loop
    )
    return {"status": "success", "incident": inc.model_dump()}


@day21_incidents_router.get("/{project_id}/incidents")
async def list_incidents(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    incidents = global_incident_service.get_incidents(project_id)
    return {"status": "success", "incidents": [i.model_dump() for i in incidents]}


@day21_incidents_router.get("/{project_id}/incidents/{incident_id}")
async def get_incident(
    project_id: str,
    incident_id: str,
    user: dict = Depends(get_current_user)
):
    incidents = global_incident_service.get_incidents(project_id)
    inc = next((i for i in incidents if i.id == incident_id), incidents[0])
    return {"status": "success", "incident": inc.model_dump()}


@day21_incidents_router.post("/{project_id}/incidents/{incident_id}/approve")
async def approve_incident_remediation(
    project_id: str,
    incident_id: str,
    user: dict = Depends(get_current_user)
):
    incidents = global_incident_service.get_incidents(project_id)
    inc = next((i for i in incidents if i.id == incident_id), incidents[0])
    res = global_incident_service.apply_and_validate_remediation(project_id, inc)
    return {"status": "success", "incident": res.model_dump()}


@day21_incidents_router.get("/{project_id}/incidents/metrics/summary")
async def get_incident_metrics(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    metrics = global_incident_service.get_metrics(project_id)
    return {"status": "success", "metrics": metrics.model_dump()}


@day21_incidents_router.post("/{project_id}/incidents/chat")
async def ask_incident_assistant(
    project_id: str,
    payload: IncidentChatPayload,
    user: dict = Depends(get_current_user)
):
    ans = global_incident_service.answer_incident_question(project_id, payload.question)
    return {"status": "success", "answer": ans}


@day21_incidents_router.get("/{project_id}/incidents/{incident_id}/report")
async def get_post_incident_report(
    project_id: str,
    incident_id: str,
    user: dict = Depends(get_current_user)
):
    rep = global_incident_service.generate_post_incident_report(project_id, incident_id)
    return {"status": "success", "report": rep.model_dump()}
