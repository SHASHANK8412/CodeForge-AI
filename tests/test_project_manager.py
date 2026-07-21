import pytest
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

def test_project_state_and_progress(tmp_path):
    state_file = tmp_path / "project_state.json"
    engine = ProjectStateEngine(state_file=str(state_file))
    
    # Update tasks
    engine.update_task("database", "Completed")
    engine.update_task("backend", "Pending")
    
    state = engine.load_state()
    assert state["tasks"]["database"]["status"] == "Completed"
    assert state["completion_percentage"] == 50.0

def test_sprint_planner():
    planner = SprintPlanner()
    tasks = ["database", "backend", "frontend", "testing"]
    
    sprints = planner.generate_sprints(tasks)
    assert len(sprints) == 2
    assert sprints[0]["sprint_name"] == "Sprint 1"
    assert sprints[0]["tasks"] == ["database", "backend", "frontend"]

def test_dependency_graph():
    graph = DependencyGraph()
    order = graph.get_execution_order()
    
    # Assert database is executed before backend
    assert order.index("database") < order.index("backend")
    # Assert backend is executed before frontend
    assert order.index("backend") < order.index("frontend")

def test_resume_engine():
    engine = ResumeEngine()
    state = {
        "tasks": {
            "database": {"status": "Completed"},
            "backend": {"status": "Failed"},
            "frontend": {"status": "Pending"}
        }
    }
    
    incomplete = engine.get_incomplete_tasks(state)
    assert incomplete == ["backend", "frontend"]

def test_bug_backlog_and_decisions():
    backlog = BugBacklog()
    backlog.log_bug("SQL Inject", "Critical", "Bypass filters")
    assert len(backlog.get_open_bugs()) == 1

    backlog.resolve_bug("SQL Inject")
    assert len(backlog.get_open_bugs()) == 0

    store = DecisionStore()
    store.record_decision("API protocol", "REST", "Accepted", "Simpler debugging")
    assert len(store.get_decisions()) == 1
    assert store.get_decisions()[0]["choice"] == "REST"

def test_standup_generator():
    generator = StandupGenerator()
    state = {
        "tasks": {
            "database": {"status": "Completed"},
            "backend": {"status": "In Progress"},
            "frontend": {"status": "Blocked"}
        }
    }
    report = generator.generate_standup_report(state)
    assert "Yesterday (Completed)" in report
    assert "database" in report
    assert "frontend" in report
