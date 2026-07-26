import time
import pytest
from fastapi.testclient import TestClient

from backend.graph.dependency import DependencyGraph
from backend.graph.parallel import ParallelExecutor, global_parallel_executor
from backend.graph.executor import WorkflowExecutor, global_workflow_executor
from backend.graph.state import WorkflowState
from backend.main import app

client = TestClient(app)


def test_dependency_graph_resolution():
    """Test 1: Verify DAG dependency resolution for sequential and parallel agents."""
    completed = set()
    ready = DependencyGraph.get_next_agents(completed)
    assert ready == ["planner"]

    completed.add("planner")
    ready = DependencyGraph.get_next_agents(completed)
    assert ready == ["architect"]

    completed.add("architect")
    ready = DependencyGraph.get_next_agents(completed)
    assert set(ready) == {"frontend", "backend", "database"}

    completed.update(["frontend", "backend", "database"])
    ready = DependencyGraph.get_next_agents(completed)
    assert ready == ["reviewer"]


def test_parallel_executor_concurrent_run():
    """Test 2: Run ParallelExecutor concurrently on frontend, backend, and database nodes."""
    executor = ParallelExecutor(timeout_seconds=60.0)
    initial_state: WorkflowState = {
        "prompt": "Food Delivery Platform",
        "session_id": "test_parallel_17",
        "architecture": {"components": ["OrderCard"], "routes": ["GET /api/orders"], "models": ["Order"]},
        "logs": []
    }

    start = time.time()
    res_state = executor.run_parallel_agents(["frontend", "backend", "database"], initial_state)
    elapsed = time.time() - start

    assert res_state["execution_status"]["frontend"] == "completed"
    assert res_state["execution_status"]["backend"] == "completed"
    assert res_state["execution_status"]["database"] == "completed"
    assert "src/App.jsx" in res_state["frontend_code"]
    assert "main.py" in res_state["backend_code"]
    assert "CREATE TABLE" in res_state["database_schema"]
    assert elapsed < 10.0


def test_output_merging():
    """Test 3: Merge parallel agent outputs into unified project_files."""
    executor = WorkflowExecutor()
    prompt = "Build a Food Delivery Platform with React, FastAPI, PostgreSQL, Stripe, and JWT"

    state = executor.execute_project_workflow(prompt, session_id="test_merge_17", use_parallel=True)

    files = state.get("project_files", {})
    assert "frontend/src/App.jsx" in files
    assert "backend/main.py" in files
    assert "database/schema.sql" in files
    assert "README.md" in files


def test_workflow_executor_parallel_mode():
    """Test 4: WorkflowExecutor parallel mode execution."""
    executor = WorkflowExecutor()
    prompt = "Food Delivery Platform"

    state = executor.execute_project_workflow(prompt, session_id="test_exec_17", use_parallel=True)
    assert state["is_complete"] is True
    assert state["progress"] == 100
    assert len(state["logs"]) >= 5


def test_project_status_api():
    """Test 5: Verify POST /generate-project and GET /project-status/{project_id} APIs."""
    res_post = client.post(
        "/api/generate-project",
        json={"prompt": "Food Delivery Platform", "session_id": "api_test_proj_17"}
    )

    assert res_post.status_code == 200
    data_post = res_post.json()
    assert data_post["status"] in ("completed", "running")
    assert data_post["project_id"] == "api_test_proj_17"

    res_get = client.get("/api/project-status/api_test_proj_17")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["project_id"] == "api_test_proj_17"
    assert data_get["status"] in ("completed", "running")


def test_sequential_vs_parallel_benchmark():
    """Test 6: Benchmark execution duration for sequential vs parallel execution modes."""
    executor = WorkflowExecutor()
    prompt = "Benchmark Food Delivery System"

    # 1. Parallel execution
    start_par = time.time()
    state_par = executor.execute_project_workflow(prompt, session_id="bm_parallel", use_parallel=True)
    duration_par = round(time.time() - start_par, 3)

    # 2. Sequential execution
    start_seq = time.time()
    state_seq = executor.execute_project_workflow(prompt, session_id="bm_sequential", use_parallel=False)
    duration_seq = round(time.time() - start_seq, 3)

    print(f"\n[BENCHMARK RESULTS] Parallel Execution: {duration_par}s | Sequential Execution: {duration_seq}s")
    assert state_par["is_complete"] is True
    assert state_seq["is_complete"] is True
