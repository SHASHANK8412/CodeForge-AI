"""
AIForge REST API — Phase 6: Autonomous AI Workflow & Automation Engine
======================================================================
Endpoints:
- GET  /api/autonomous-workflows
- GET  /api/autonomous-workflows/{workflow_id}
- POST /api/autonomous-workflows/dispatch
- POST /api/autonomous-workflows/{workflow_id}/approve-step
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, status
from pydantic import BaseModel, Field

from backend.workflow_engine.autonomous_runtime import global_autonomous_engine, TriggerType

router = APIRouter(prefix="/api/autonomous-workflows", tags=["AIForge Autonomous AI Workflow Engine"])


class DispatchWorkflowPayload(BaseModel):
    goal: str
    trigger_type: Optional[str] = "MANUAL"


class ApproveStepPayload(BaseModel):
    step_id: str


@router.get("")
def list_autonomous_workflows():
    wfs = global_autonomous_engine.list_workflows()
    return {
        "success": True,
        "count": len(wfs),
        "workflows": [w.model_dump() for w in wfs]
    }


@router.get("/{workflow_id}")
def get_autonomous_workflow(workflow_id: str):
    wf = global_autonomous_engine.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Autonomous Workflow '{workflow_id}' not found")
    return {
        "success": True,
        "workflow": wf.model_dump()
    }


@router.post("/dispatch", status_code=status.HTTP_201_CREATED)
def dispatch_workflow(payload: DispatchWorkflowPayload):
    if not payload.goal.strip():
        raise HTTPException(status_code=400, detail="Goal cannot be empty")

    wf = global_autonomous_engine.plan_and_dispatch_workflow(
        goal=payload.goal,
        trigger_type=TriggerType(payload.trigger_type or "MANUAL")
    )
    return {
        "success": True,
        "workflow": wf.model_dump()
    }


@router.post("/{workflow_id}/approve-step")
def approve_workflow_step(workflow_id: str, payload: ApproveStepPayload):
    res = global_autonomous_engine.approve_workflow_step(workflow_id, payload.step_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message", "Failed to approve step"))
    return res
