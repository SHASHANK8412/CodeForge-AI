import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.project_manager.planner import global_project_planner

logger = logging.getLogger("aiforge.routes.project_manager")

router = APIRouter(tags=["Autonomous Project Management & Sprint Orchestration"])


class CreateProjectPlanRequest(BaseModel):
    prompt: str = Field(min_length=1)


@router.post("/project/create")
@router.post("/api/project/create")
def create_project_plan(req: CreateProjectPlanRequest):
    """Decomposes prompt into Product Manager Analysis, Epics, Stories, Tasks, DAG & Sprints."""
    return global_project_planner.plan_project(req.prompt)


@router.get("/project/{id}")
@router.get("/api/project/{id}")
def get_project_details(id: str):
    """Returns project details for a given project ID."""
    return global_project_planner.plan_project(f"Project {id}")


@router.get("/project/tasks")
@router.get("/api/project/tasks")
def get_project_tasks(prompt: str = "Build Application"):
    """Returns task breakdown for a project."""
    plan = global_project_planner.plan_project(prompt)
    return {"tasks": plan["tasks"]}


@router.get("/project/sprints")
@router.get("/api/project/sprints")
def get_project_sprints(prompt: str = "Build Application"):
    """Returns sprint allocation for a project."""
    plan = global_project_planner.plan_project(prompt)
    return {"sprints": plan["sprints"]}


@router.get("/project/progress")
@router.get("/api/project/progress")
def get_project_progress(prompt: str = "Build Application"):
    """Returns project progress metrics."""
    plan = global_project_planner.plan_project(prompt)
    return plan["progress"]


@router.get("/project/analytics")
@router.get("/api/project/analytics")
def get_project_analytics(prompt: str = "Build Application"):
    """Returns burndown & velocity analytics."""
    plan = global_project_planner.plan_project(prompt)
    return plan["analytics"]
