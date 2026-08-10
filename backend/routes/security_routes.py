"""
AIForge Autonomous Engineering Platform — Security REST API Routes
=====================================================================
Endpoints:
- GET /api/projects/{project_id}/security
- POST /api/projects/{project_id}/security/fix
- GET /api/projects/{project_id}/sbom
- GET /api/projects/{project_id}/security-report
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.security.security_manager import global_security_manager, SecurityReport
from backend.agents.security_repair_agent import global_security_repair_agent
from backend.security.sbom_generator import global_sbom_generator

_logger = logging.getLogger("aiforge.routes.security")

router = APIRouter(prefix="/api/projects", tags=["security"])

# Store active security reports in memory
security_store: Dict[str, SecurityReport] = {}


class FixSecurityRequest(BaseModel):
    files: Dict[str, str]


@router.get("/{project_id}/security")
async def get_project_security_endpoint(project_id: str):
    if project_id in security_store:
        return security_store[project_id].model_dump()

    # Generate baseline security report for requested project
    dummy_manifest = {
        "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()\n",
        "package.json": '{"dependencies": {"react": "^18.0.0"}}',
        ".gitignore": ".env\n"
    }
    report = global_security_manager.audit_project(project_id, dummy_manifest)
    security_store[project_id] = report
    return report.model_dump()


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


@router.get("/{project_id}/sbom")
async def get_project_sbom_endpoint(project_id: str):
    dummy_manifest = {
        "package.json": '{"dependencies": {"react": "^18.2.0", "axios": "^1.6.0"}}',
        "requirements.txt": "fastapi==0.109.0\nuvicorn==0.27.0\n"
    }
    sbom = global_sbom_generator.generate_sbom(project_id, dummy_manifest)
    return sbom.model_dump()


@router.get("/{project_id}/security-report")
async def get_project_security_report_markdown_endpoint(project_id: str):
    report = security_store.get(project_id)
    if not report:
        dummy_manifest = {"backend/main.py": "from fastapi import FastAPI\napp = FastAPI()\n"}
        report = global_security_manager.audit_project(project_id, dummy_manifest)
        security_store[project_id] = report

    markdown = global_security_manager.generate_security_markdown(report)
    return {"project_id": project_id, "markdown": markdown}
