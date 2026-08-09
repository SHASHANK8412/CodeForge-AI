"""
AIForge V2 — Security Foundation REST API Routes
================================================
Endpoints for security scanning, secret detection, dependency audits,
false positive marking, and security reports.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user
from backend.security.service import global_security_service
from backend.security.rate_limiter import global_rate_limiter

security_router = APIRouter(prefix="/api/security", tags=["Security Center"])


class FalsePositivePayload(BaseModel):
    finding_id: str
    reason: str


@security_router.post("/scan")
async def scan_project_security(
    project_id: str = Query("aiforge-demo"),
    user: dict = Depends(get_current_user)
):
    global_rate_limiter.check(f"sec_scan_{user.get('id', 'anon')}")
    # Sample files map for scan
    sample_files = {
        "backend/auth.py": "def login(username, password):\n    # TODO: add role check\n    pass",
        "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()",
        "requirements.txt": "fastapi==0.109.0\npyaml==5.3.1\nrequests==2.25.0\n",
    }
    report = global_security_service.run_full_security_scan(project_id, sample_files, user.get("id", "demo_user"))
    return {"status": "success", "report": report.model_dump()}


@security_router.get("/{project_id}/report")
async def get_project_security_report(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    sample_files = {
        "backend/auth.py": "def login(username, password):\n    # TODO: add role check\n    pass",
        "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()",
        "requirements.txt": "fastapi==0.109.0\npyaml==5.3.1\nrequests==2.25.0\n",
    }
    report = global_security_service.run_full_security_scan(project_id, sample_files, user.get("id", "demo_user"))
    return {"status": "success", "report": report.model_dump()}


@security_router.post("/{project_id}/false-positive")
async def mark_false_positive(
    project_id: str,
    payload: FalsePositivePayload,
    user: dict = Depends(get_current_user)
):
    success = global_security_service.mark_false_positive(
        project_id, payload.finding_id, payload.reason, user.get("id", "demo_user")
    )
    return {"status": "success", "marked": success}
