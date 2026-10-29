"""
AIForge REST API — Sentinel Cybersecurity Platform & AI-SOC
============================================================
Endpoints:
- GET /api/sentinel/posture
- POST /api/sentinel/audit
- POST /api/sentinel/remediate
- GET /api/sentinel/threat-model
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, status
from pydantic import BaseModel, Field

from backend.security.sentinel_service import global_sentinel_service

router = APIRouter(prefix="/api/sentinel", tags=["AIForge Sentinel (AI-SOC)"])


class AuditProjectPayload(BaseModel):
    project_id: Optional[str] = "aiforge-fooddelivery-ai"


class RemediatePayload(BaseModel):
    project_id: str = "aiforge-fooddelivery-ai"
    finding_id: str
    approved: bool = True


@router.get("/posture")
def get_security_posture(project_id: Optional[str] = Query("aiforge-fooddelivery-ai")):
    report = global_sentinel_service.get_security_posture(project_id=project_id)
    return {
        "success": True,
        "posture": report.model_dump()
    }


@router.post("/audit", status_code=status.HTTP_200_OK)
def run_security_audit(payload: AuditProjectPayload):
    report = global_sentinel_service.run_full_security_audit(project_id=payload.project_id or "aiforge-fooddelivery-ai")
    return {
        "success": True,
        "posture": report.model_dump()
    }


@router.post("/remediate")
def remediate_security_finding(payload: RemediatePayload):
    res = global_sentinel_service.remediate_finding(
        project_id=payload.project_id,
        finding_id=payload.finding_id,
        approved=payload.approved
    )
    if not res.get("success"):
        raise HTTPException(status_code=404, detail=res.get("error", "Remediation failed"))
    return res
