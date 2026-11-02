"""
AIForge REST API — Deep Research Engine
=======================================
Endpoints:
- GET /api/research
- GET /api/research/{report_id}
- POST /api/research/run
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, status
from pydantic import BaseModel, Field

from backend.research.deep_research_service import (
    global_research_service,
    DeepResearchReport
)

router = APIRouter(prefix="/api/research", tags=["Deep Research Engine"])


class RunResearchPayload(BaseModel):
    topic: str
    project_id: Optional[str] = "aiforge-fooddelivery-ai"


@router.get("")
def list_research_reports(project_id: Optional[str] = Query(None)):
    reports = global_research_service.list_reports(project_id=project_id)
    return {
        "success": True,
        "count": len(reports),
        "reports": [r.model_dump() for r in reports]
    }


@router.get("/{report_id}")
def get_research_report(report_id: str):
    r = global_research_service.get_report(report_id)
    if not r:
        raise HTTPException(status_code=404, detail=f"Research report '{report_id}' not found")
    return {
        "success": True,
        "report": r.model_dump()
    }


@router.post("/run", status_code=status.HTTP_201_CREATED)
def run_deep_research(payload: RunResearchPayload):
    if not payload.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty")

    report = global_research_service.run_deep_research(
        topic=payload.topic,
        project_id=payload.project_id
    )
    return {
        "success": True,
        "report": report.model_dump()
    }
