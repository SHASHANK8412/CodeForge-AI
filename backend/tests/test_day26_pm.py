import pytest
from fastapi.testclient import TestClient

from backend.agents.product_manager import ProductManagerAgent
from backend.project_manager.epics import EpicGenerator
from backend.project_manager.stories import UserStoryGenerator
from backend.project_manager.tasks import TaskBreakdownEngine
from backend.project_manager.dependency_graph import ProjectDependencyGraph
from backend.project_manager.sprint import SprintPlanner
from backend.project_manager.tracker import ProgressTracker
from backend.project_manager.planner import ProjectPlanner
from backend.main import app

client = TestClient(app)


def test_product_manager_agent():
    """Test 1: ProductManagerAgent requirements decomposition and architecture recommendation."""
    pm = ProductManagerAgent()

    analysis = pm.analyze_requirements("Build Banking Platform")
    assert "functional_requirements" in analysis
    assert len(analysis["functional_requirements"]) >= 3
    assert "FastAPI" in analysis["recommended_stack"]


def test_epic_generator():
    """Test 2: EpicGenerator epic generation (EP-01..EP-05)."""
    epic_gen = EpicGenerator()

    epics = epic_gen.generate_epics("Build E-Commerce Platform")
    assert len(epics) >= 5
    assert epics[0]["id"] == "EP-01"


def test_user_story_generator():
    """Test 3: UserStoryGenerator story creation and story points."""
    epic_gen = EpicGenerator()
    story_gen = UserStoryGenerator()

    epics = epic_gen.generate_epics("Build App")
    stories = story_gen.generate_stories(epics)
    assert len(stories) >= 5
    assert stories[0]["id"].startswith("US-")
    assert stories[0]["points"] > 0


def test_task_breakdown_engine_and_dag():
    """Test 4: TaskBreakdownEngine task decomposition, agent assignment, and DAG generation."""
    task_eng = TaskBreakdownEngine()
    dag_builder = ProjectDependencyGraph()

    stories = [{"id": "US-01", "epic_id": "EP-01", "title": "Registration"}]
    tasks = task_eng.generate_tasks(stories)
    assert len(tasks) >= 3
    assert "agent" in tasks[0]

    dag = dag_builder.build_dag(tasks)
    assert dag["node_count"] == len(tasks)
    assert dag["has_cycles"] is False


def test_sprint_planner_and_tracker():
    """Test 5: SprintPlanner sprint allocation and ProgressTracker metrics."""
    task_eng = TaskBreakdownEngine()
    sprint_plan = SprintPlanner()
    tracker = ProgressTracker()

    tasks = task_eng.generate_tasks([])
    sprints = sprint_plan.plan_sprints(tasks)
    assert len(sprints) == 3

    progress = tracker.track_progress(tasks)
    assert progress["progress_percentage"] >= 0.0


def test_project_manager_api_endpoints():
    """Test 6: FastAPI Project Manager endpoints (/api/project/create, /api/project/tasks, /api/project/sprints, /api/project/progress)."""
    # 1. POST /api/project/create
    res_create = client.post("/api/project/create", json={"prompt": "Build AI Resume Analyzer"})
    assert res_create.status_code == 200
    assert len(res_create.json()["epics"]) >= 5

    # 2. GET /api/project/tasks
    res_tasks = client.get("/api/project/tasks")
    assert res_tasks.status_code == 200
    assert "tasks" in res_tasks.json()

    # 3. GET /api/project/sprints
    res_sprints = client.get("/api/project/sprints")
    assert res_sprints.status_code == 200
    assert "sprints" in res_sprints.json()

    # 4. GET /api/project/progress
    res_progress = client.get("/api/project/progress")
    assert res_progress.status_code == 200
    assert "progress_percentage" in res_progress.json()
