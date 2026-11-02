"""
AIForge REST API — Phase 7: Autonomous AI Operating System (AIForge OS)
=======================================================================
Endpoints:
- GET  /api/os/overview
- POST /api/os/command
- GET  /api/os/goals
- POST /api/os/goals
- POST /api/os/emergency-stop
- POST /api/os/resume
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, status
from pydantic import BaseModel, Field

from backend.ai_os.kernel import global_aiforge_os_kernel, AutonomyLevel

router = APIRouter(prefix="/api/os", tags=["AIForge Autonomous AI Operating System (AIForge OS)"])


class CommandPayload(BaseModel):
    command: str


class GoalPayload(BaseModel):
    objective: str
    autonomy_level: Optional[str] = "LEVEL_2_APPROVAL_REQUIRED"


@router.get("/overview")
def get_os_overview():
    return {
        "success": True,
        "overview": global_aiforge_os_kernel.get_system_overview()
    }


@router.post("/command")
def execute_universal_command(payload: CommandPayload):
    if not payload.command.strip():
        raise HTTPException(status_code=400, detail="Command cannot be empty")

    res = global_aiforge_os_kernel.execute_universal_command(payload.command)
    return {
        "success": True,
        "result": res
    }


@router.get("/goals")
def list_goals():
    goals = global_aiforge_os_kernel.list_goals()
    return {
        "success": True,
        "count": len(goals),
        "goals": [g.model_dump() for g in goals]
    }


@router.post("/goals", status_code=status.HTTP_201_CREATED)
def dispatch_goal(payload: GoalPayload):
    if not payload.objective.strip():
        raise HTTPException(status_code=400, detail="Objective cannot be empty")

    goal = global_aiforge_os_kernel.dispatch_autonomous_goal(
        objective=payload.objective,
        autonomy_level=AutonomyLevel(payload.autonomy_level or "LEVEL_2_APPROVAL_REQUIRED")
    )
    return {
        "success": True,
        "goal": goal.model_dump()
    }


@router.post("/emergency-stop")
def trigger_emergency_stop():
    return global_aiforge_os_kernel.trigger_emergency_stop()


@router.post("/resume")
def resume_system():
    return global_aiforge_os_kernel.resume_system()
