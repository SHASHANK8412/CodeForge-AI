"""
AIForge REST API — Phase 4: AI Cybersecurity Copilot & Autonomous Defense
========================================================================
Endpoints:
- GET  /api/cyber-copilot/overview
- GET  /api/cyber-copilot/incidents
- GET  /api/cyber-copilot/incidents/{incident_id}
- POST /api/cyber-copilot/investigate
- POST /api/cyber-copilot/incidents/{incident_id}/approve-remediation
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, status
from pydantic import BaseModel, Field

from backend.security.cyber_copilot_service import global_cyber_copilot

router = APIRouter(prefix="/api/cyber-copilot", tags=["AIForge AI Cybersecurity Copilot"])


class InvestigatePayload(BaseModel):
    query: str


class ApproveRemediationPayload(BaseModel):
    remediation_id: str


@router.get("/overview")
def get_soc_overview():
    return {
        "success": True,
        "overview": global_cyber_copilot.get_soc_overview()
    }


@router.get("/incidents")
def list_security_incidents():
    incidents = global_cyber_copilot.list_incidents()
    return {
        "success": True,
        "count": len(incidents),
        "incidents": [i.model_dump() for i in incidents]
    }


@router.get("/incidents/{incident_id}")
def get_incident_details(incident_id: str):
    inc = global_cyber_copilot.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Security Incident '{incident_id}' not found")
    return {
        "success": True,
        "incident": inc.model_dump()
    }


@router.post("/investigate")
def run_security_investigation(payload: InvestigatePayload):
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    res = global_cyber_copilot.run_ai_investigation(payload.query)
    return {
        "success": True,
        "investigation": res
    }


@router.post("/incidents/{incident_id}/approve-remediation")
def approve_remediation_action(incident_id: str, payload: ApproveRemediationPayload):
    res = global_cyber_copilot.approve_remediation(incident_id, payload.remediation_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message", "Failed to approve remediation"))
    return res
