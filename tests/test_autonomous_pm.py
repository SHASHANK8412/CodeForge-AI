"""
Test suite for the AutonomousProjectManager.
Validates roadmap generation, parallel scheduling, ETA prediction,
risk analysis, blocker detection, auto-replan, resume, and reporting.
"""
import pytest
import tempfile
from pathlib import Path
from backend.project_manager.autonomous_manager import AutonomousProjectManager


@pytest.fixture
def pm(tmp_path):
    state_file = str(tmp_path / "project_state.json")
    return AutonomousProjectManager(state_file=state_file)


def test_roadmap_generation(pm):
    roadmap = pm.generate_roadmap("Build an E-Commerce Website")
    assert roadmap["project_name"] == "Build an E-Commerce Website"
    assert len(roadmap["milestones"]) >= 3
    assert len(roadmap["phases"]) == 5
    assert len(roadmap["dependency_order"]) >= 6
    assert len(roadmap["parallel_schedule"]) >= 1
    assert len(roadmap["agent_assignments"]) >= 6
    assert len(roadmap["sprint_plan"]) >= 1
    assert roadmap["eta"]["parallel_estimate_s"] > 0
    assert roadmap["eta"]["speedup_factor"] >= 1.0
    assert len(roadmap["risk_analysis"]) >= 1
    assert roadmap["recovery_plan"]["max_retries"] == 3
    assert roadmap["progress"]["total_tasks"] >= 6


def test_parallel_schedule_respects_deps(pm):
    roadmap = pm.generate_roadmap("Hospital Management System")
    layers = roadmap["parallel_schedule"]
    # First layer should contain database (no deps)
    assert "database" in layers[0]["parallel_tasks"]
    # Frontend should NOT appear before backend
    frontend_layer = next(
        (i for i, l in enumerate(layers) if "frontend" in l["parallel_tasks"]), 999
    )
    backend_layer = next(
        (i for i, l in enumerate(layers) if "backend" in l["parallel_tasks"]), 999
    )
    assert frontend_layer > backend_layer


def test_eta_prediction(pm):
    roadmap = pm.generate_roadmap("Todo App")
    eta = roadmap["eta"]
    assert eta["sequential_estimate_s"] >= eta["parallel_estimate_s"]
    assert eta["speedup_factor"] >= 1.0
    assert len(eta["layer_breakdown"]) >= 1


def test_risk_analysis(pm):
    roadmap = pm.generate_roadmap("Social Media Platform")
    risks = roadmap["risk_analysis"]
    assert len(risks) >= 1
    # backend/frontend are slow => should have duration risk
    duration_risks = [r for r in risks if "duration" in r["risk"]]
    assert len(duration_risks) >= 1


def test_progress_tracking(pm):
    pm.generate_roadmap("Progress Test Project")
    snapshot = pm._get_progress_snapshot()
    assert snapshot["total_tasks"] >= 6
    assert snapshot["completed"] == 0
    assert snapshot["pending"] >= 6

    pm.complete_task("database", "Tables provisioned")
    snapshot2 = pm._get_progress_snapshot()
    assert snapshot2["completed"] == 1
    assert snapshot2["completion_percentage"] > 0


def test_blocker_detection_and_replan(pm):
    pm.generate_roadmap("Blocker Test")
    pm.block_task("backend", "API timeout failure")
    pm.fail_task("frontend", "Build crash")

    result = pm.detect_and_replan()
    assert "backend" in result["blockers"]
    assert "frontend" in result["blockers"]
    assert result["action"] == "Replanned"
    assert len(result["new_schedule"]) >= 2


def test_resume_interrupted_work(pm):
    pm.generate_roadmap("Resume Test")
    pm.complete_task("database")
    pm.complete_task("backend")

    resume_info = pm.resume()
    assert resume_info["status"] == "Resuming"
    assert "database" not in resume_info["remaining_tasks"]
    assert "backend" not in resume_info["remaining_tasks"]
    assert resume_info["progress"]["completed"] == 2


def test_daily_report(pm):
    pm.generate_roadmap("Report Test")
    pm.complete_task("database")
    pm.start_task("backend")
    pm.block_task("frontend", "Waiting on API")

    report = pm.generate_daily_report()
    assert "standup" in report
    assert report["progress"]["completed"] == 1
    assert report["progress"]["in_progress"] == 1
    assert report["progress"]["blocked"] == 1


def test_never_repeats_completed_work(pm):
    pm.generate_roadmap("No Repeat Test")
    pm.complete_task("database")
    pm.complete_task("backend")

    # Generate roadmap again — completed tasks must stay completed
    pm.generate_roadmap("No Repeat Test")
    state = pm.state_engine.load_state()
    assert state["tasks"]["database"]["status"] == "Completed"
    assert state["tasks"]["backend"]["status"] == "Completed"
