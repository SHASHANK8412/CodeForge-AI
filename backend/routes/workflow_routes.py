"""
AIForge REST API — Visual AI Workflow Builder
==============================================
Endpoints:
- GET /api/workflows
- GET /api/workflows/{workflow_id}
- POST /api/workflows
- POST /api/workflows/{workflow_id}/run
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, status
from pydantic import BaseModel, Field

from backend.workflows.workflow_builder_service import (
    global_workflow_service,
    AIWorkflow
)

router = APIRouter(prefix="/api/workflows", tags=["AI Workflow Builder"])


class CreateWorkflowPayload(BaseModel):
    title: str
    description: str = ""
    trigger_type: str = "MANUAL"
    schedule_cron: Optional[str] = None
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    project_id: Optional[str] = "aiforge-fooddelivery-ai"


@router.get("")
def list_workflows(project_id: Optional[str] = Query(None)):
    items = global_workflow_service.list_workflows(project_id=project_id)
    return {
        "success": True,
        "count": len(items),
        "workflows": [w.model_dump() for w in items]
    }


@router.get("/{workflow_id}")
def get_workflow(workflow_id: str):
    w = global_workflow_service.get_workflow(workflow_id)
    if not w:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")
    return {
        "success": True,
        "workflow": w.model_dump()
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_workflow(payload: CreateWorkflowPayload):
    if not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    w = global_workflow_service.create_workflow(
        title=payload.title,
        description=payload.description,
        trigger_type=payload.trigger_type,
        schedule_cron=payload.schedule_cron,
        nodes=payload.nodes,
        project_id=payload.project_id
    )
    return {
        "success": True,
        "workflow": w.model_dump()
    }


@router.post("/{workflow_id}/run")
def execute_workflow(workflow_id: str):
    res = global_workflow_service.execute_workflow(workflow_id)
    if not res.get("success"):
        raise HTTPException(status_code=404, detail=res.get("error", "Execution failed"))
    return res
