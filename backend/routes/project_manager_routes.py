"""
FastAPI Routes for Day 29 Autonomous Project Manager Agent
===========================================================
Exposes REST APIs for autonomous project sprint management, milestone status, task assignments, daily executive reporting, and project dashboard metrics.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import time

from backend.agents.project_manager_agent import global_project_manager_agent

router = APIRouter(tags=["Autonomous Project Manager Agent"])


class StartProjectRequest(BaseModel):
    project_name: str
    prompt: Optional[str] = ""


# In-memory store for project manager runtime states
_active_pm_sessions: Dict[str, Dict[str, Any]] = {}


def _get_or_create_pm_session(project_name: str) -> Dict[str, Any]:
    if project_name not in _active_pm_sessions:
        milestones = global_project_manager_agent.break_into_milestones(project_name)
        all_tasks = []
        for m in milestones:
            ts = global_project_manager_agent.divide_milestone_into_tasks(m["id"], m["title"])
            all_tasks.extend(ts)

        assigned_tasks = global_project_manager_agent.assign_agents(all_tasks)
        
        # Mark first few tasks done to demonstrate live tracking
        if len(assigned_tasks) > 2:
            assigned_tasks[0]["status"] = "Completed"
            assigned_tasks[1]["status"] = "Completed"
            assigned_tasks[2]["status"] = "In Progress"

        _active_pm_sessions[project_name] = {
            "project_name": project_name,
            "created_at": time.time(),
            "milestones": milestones,
            "tasks": assigned_tasks,
            "current_agent": "Frontend Agent",
            "current_sprint": "Sprint 1: Core Setup & Auth",
            "logs": [
                f"{time.strftime('%H:%M')} - Project initialized",
                f"{time.strftime('%H:%M')} - Planner completed",
                f"{time.strftime('%H:%M')} - Milestones breakdown completed",
                f"{time.strftime('%H:%M')} - Architecture completed",
                f"{time.strftime('%H:%M')} - Frontend Agent started"
            ]
        }
    return _active_pm_sessions[project_name]


@router.post("/project/start")
@router.post("/api/v1/project/start")
async def start_autonomous_project(req: StartProjectRequest) -> Dict[str, Any]:
    """Starts autonomous engineering sprint for a project, creating milestones & assigning tasks."""
    try:
        session = _get_or_create_pm_session(req.project_name)
        progress_json = global_project_manager_agent.generate_progress_json(
            req.project_name, session["tasks"], session["current_agent"]
        )
        return {
            "status": "success",
            "message": f"Autonomous sprint started for project '{req.project_name}'",
            "project_name": req.project_name,
            "milestones_count": len(session["milestones"]),
            "tasks_count": len(session["tasks"]),
            "progress_json": progress_json
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project/status")
@router.get("/api/v1/project/status")
async def get_project_status(project_name: Optional[str] = "Food Delivery App") -> Dict[str, Any]:
    """Retrieves real-time Progress JSON, current agent, progress percentage, and ASCII progress bar."""
    session = _get_or_create_pm_session(project_name)
    progress_json = global_project_manager_agent.generate_progress_json(
        project_name, session["tasks"], session["current_agent"]
    )
    return {"status": "success", "progress_json": progress_json}


@router.get("/project/report")
@router.get("/api/v1/project/report")
async def get_project_daily_report(project_name: Optional[str] = "Food Delivery App") -> Dict[str, Any]:
    """Generates executive Daily Report detailing completed, running, and pending tasks."""
    session = _get_or_create_pm_session(project_name)
    report = global_project_manager_agent.generate_daily_report(project_name, session["tasks"])
    return {"status": "success", "daily_report": report}


@router.get("/project/tasks")
@router.get("/api/v1/project/tasks")
async def get_project_tasks(project_name: Optional[str] = "Food Delivery App") -> Dict[str, Any]:
    """Retrieves all milestone tasks, agent assignments, and status breakdown."""
    session = _get_or_create_pm_session(project_name)
    metrics = global_project_manager_agent.monitor_completion(session["tasks"])
    blockers = global_project_manager_agent.detect_blockers(session["tasks"])
    return {
        "status": "success",
        "project_name": project_name,
        "metrics": metrics,
        "tasks": session["tasks"],
        "blockers": blockers
    }


@router.get("/project/dashboard")
@router.get("/api/v1/project/dashboard")
async def get_project_dashboard(project_name: Optional[str] = "Food Delivery App") -> Dict[str, Any]:
    """Retrieves Project Dashboard metrics: Current Sprint, Current Agent, Progress Bar, Completed/Pending Tasks, Logs, Estimated Completion Time."""
    session = _get_or_create_pm_session(project_name)
    progress_json = global_project_manager_agent.generate_progress_json(
        project_name, session["tasks"], session["current_agent"]
    )
    completed_tasks = [t for t in session["tasks"] if t.get("status") in ["Completed", "Done"]]
    pending_tasks = [t for t in session["tasks"] if t.get("status") != "Completed" and t.get("status") != "Done"]

    return {
        "status": "success",
        "dashboard": {
            "project_name": project_name,
            "current_sprint": session["current_sprint"],
            "current_agent": session["current_agent"],
            "progress_percentage": progress_json["progress"],
            "progress_bar": progress_json["progress_bar"],
            "completed_tasks_count": len(completed_tasks),
            "pending_tasks_count": len(pending_tasks),
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "logs": session["logs"],
            "estimated_completion_time": "12 minutes"
        }
    }
