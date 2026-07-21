from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from pathlib import Path

from backend.project_manager.state_engine import ProjectStateEngine
from backend.project_manager.sprint_planner import SprintPlanner
from backend.project_manager.dependency_graph import DependencyGraph
from backend.project_manager.task_scheduler import TaskScheduler
from backend.project_manager.progress_tracker import ProgressTracker
from backend.project_manager.resume_engine import ResumeEngine
from backend.project_manager.bug_backlog import BugBacklog
from backend.project_manager.milestone_generator import MilestoneGenerator
from backend.project_manager.decision_store import DecisionStore
from backend.project_manager.standup_generator import StandupGenerator

router = APIRouter(prefix="/project", tags=["Project Manager"])

# Instantiate state helpers
workspace_root = Path(__file__).resolve().parents[2]
state_file = workspace_root / "backend" / "project_manager" / "project_state.json"

state_engine = ProjectStateEngine(state_file=str(state_file))
sprint_planner = SprintPlanner()
dep_graph = DependencyGraph()
task_scheduler = TaskScheduler()
progress_tracker = ProgressTracker()
resume_engine = ResumeEngine()
bug_backlog = BugBacklog()
milestone_gen = MilestoneGenerator()
decision_store = DecisionStore()
standup_gen = StandupGenerator()

# Seed default data
bug_backlog.log_bug("CORS wildcard config", "High", "Update to secure origins list.")
decision_store.record_decision("Auth Mechanism", "JWT Stateless Tokens", "Accepted", "Stateless scaling")

class TaskUpdateRequest(BaseModel):
    task_name: str
    status: str
    details: str = ""

@router.get("/state")
def get_project_state():
    return state_engine.load_state()

@router.post("/task")
def update_task_state(req: TaskUpdateRequest):
    state_engine.update_task(req.task_name, req.status, req.details)
    return {"message": f"Task '{req.task_name}' updated successfully."}

@router.get("/sprints")
def get_sprints():
    tasks = list(state_engine.load_state().get("tasks", {}).keys())
    if not tasks:
        tasks = ["database", "backend", "frontend", "testing", "deployment", "documentation"]
    return sprint_planner.generate_sprints(tasks)

@router.get("/milestones")
def get_milestones():
    tasks = ["database", "backend", "frontend", "testing", "deployment", "documentation"]
    return milestone_gen.generate_milestones(tasks)

@router.get("/standup")
def get_daily_standup():
    state = state_engine.load_state()
    return {"standup": standup_gen.generate_standup_report(state)}

@router.get("/bugs")
def get_bugs():
    return bug_backlog.get_open_bugs()

@router.get("/decisions")
def get_decisions():
    return decision_store.get_decisions()
