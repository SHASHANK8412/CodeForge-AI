"""
AIForge Autonomous Engineering Platform — Security REST API Routes
=====================================================================
Endpoints:
- POST /api/projects/{project_id}/security/fix   (audits and repairs the files sent in the request)

The GET /security, /sbom and /security-report endpoints audited hardcoded sample manifests and were
retired; project assessments and reports are served by the Security Guardian
(/api/projects/{project_id}/guardian/...).
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.security.security_manager import global_security_manager, SecurityReport
from backend.agents.security_repair_agent import global_security_repair_agent

_logger = logging.getLogger("aiforge.routes.security")

router = APIRouter(prefix="/api/projects", tags=["security"])

# Store active security reports in memory
security_store: Dict[str, SecurityReport] = {}


class FixSecurityRequest(BaseModel):
    files: Dict[str, str]


@router.post("/{project_id}/security/fix")
async def fix_project_security_endpoint(project_id: str, req: FixSecurityRequest):
    _logger.info(f"API: Auto-remediating security issues for '{project_id}'...")

    report = global_security_manager.audit_project(project_id, req.files)
    fix_result = global_security_repair_agent.fix_security_issues(report.findings, req.files)

    # Re-audit after fixes
    re_report = global_security_manager.audit_project(project_id, req.files)
    security_store[project_id] = re_report

    return {
        "status": "success",
        "project_id": project_id,
        "fix_result": fix_result.model_dump(),
        "re_audit": re_report.model_dump(),
        "modified_files": req.files
    }
