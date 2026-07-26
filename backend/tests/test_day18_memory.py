import pytest
from fastapi.testclient import TestClient

from backend.memory.short_term import ShortTermMemory
from backend.memory.long_term import LongTermMemory
from backend.memory.versioning import VersionControlManager
from backend.memory.manager import CentralMemoryManager, central_memory_manager
from backend.main import app

client = TestClient(app)


def test_short_term_memory():
    """Test 1: ShortTermMemory storage and retrieval during active task."""
    st = ShortTermMemory()
    st.set("active_step", "frontend_generation")
    st.set("planner_plan", {"project_name": "E-Commerce"})

    assert st.get("active_step") == "frontend_generation"
    assert st.get("planner_plan")["project_name"] == "E-Commerce"

    st.clear()
    assert st.get("active_step") is None


def test_long_term_memory_persistence(tmp_path):
    """Test 2: LongTermMemory project save, load, update, and delete."""
    storage_file = tmp_path / "test_projects.json"
    lt = LongTermMemory(storage_file=storage_file)

    p1 = lt.save_project("proj_001", {
        "name": "E-Commerce Platform",
        "prompt": "Build an E-Commerce Platform with FastAPI and PostgreSQL",
        "tech_stack": {"frontend": "React", "backend": "FastAPI", "database": "PostgreSQL"}
    })

    assert p1["name"] == "E-Commerce Platform"
    assert lt.get_project("proj_001")["tech_stack"]["backend"] == "FastAPI"

    lt.update_project("proj_001", {"name": "E-Commerce V2"})
    assert lt.get_project("proj_001")["name"] == "E-Commerce V2"

    deleted = lt.delete_project("proj_001")
    assert deleted is True
    assert lt.get_project("proj_001") is None


def test_version_control_tracking():
    """Test 3: VersionControlManager snapshot tracking (v1, v2, v3)."""
    vcm = VersionControlManager()
    p_id = "test_version_proj"

    v1 = vcm.create_version(p_id, "Initial Commit", {"src/App.jsx": "code_v1"})
    assert v1["version"] == "v1"

    v2 = vcm.create_version(p_id, "Add JWT Auth", {"src/App.jsx": "code_v2", "main.py": "auth_v2"})
    assert v2["version"] == "v2"

    versions = vcm.list_versions(p_id)
    assert len(versions) == 2
    assert versions[0]["version"] == "v1"
    assert versions[1]["version"] == "v2"


def test_semantic_memory_search(tmp_path):
    """Test 4: Semantic memory search over project titles and tech stacks."""
    storage_file = tmp_path / "search_projects.json"
    lt = LongTermMemory(storage_file=storage_file)

    lt.save_project("hosp_01", {"name": "Hospital System", "prompt": "Patient management with JWT authentication"})
    lt.save_project("food_02", {"name": "Food Delivery App", "prompt": "Order food online using Stripe payments"})

    results = lt.search_semantic("JWT authentication", top_k=1)
    assert len(results) == 1
    assert "Hospital" in results[0]["name"]


def test_memory_crud_api_routes():
    """Test 5: FastAPI Memory CRUD endpoints (/api/memory/save, /api/memory/projects, /api/memory/search)."""
    save_res = client.post(
        "/api/memory/save",
        json={
            "project_id": "api_mem_test_01",
            "name": "Banking Application",
            "prompt": "Secure banking portal with JWT auth and PostgreSQL",
            "tech_stack": {"backend": "FastAPI", "database": "PostgreSQL"}
        }
    )
    assert save_res.status_code == 200
    assert save_res.json()["status"] == "success"

    list_res = client.get("/api/memory/projects")
    assert list_res.status_code == 200
    projects = list_res.json()
    assert any(p["project_id"] == "api_mem_test_01" for p in projects)

    search_res = client.get("/api/memory/search?query=banking")
    assert search_res.status_code == 200
    s_data = search_res.json()
    assert s_data["count"] >= 1


def test_project_resume_workflow():
    """Test 6: Resume project workflow (version increment v1 -> v2 & memory loading)."""
    central_memory_manager.save_project("resume_proj_18", {
        "name": "Todo Platform",
        "prompt": "Build initial Todo App",
        "version": "v1"
    })

    resumed = central_memory_manager.resume_project("resume_proj_18", "Add Category Organization and JWT Auth")
    assert resumed["version"] == "v2"
    assert "Follow-up: Add Category Organization" in resumed["prompt"]
