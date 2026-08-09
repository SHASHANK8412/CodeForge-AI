"""
Unit and Integration Tests for AIForge StructuredProjectBuilder & Disk Writing (Phase 5)
"""

import shutil
import pytest
from pathlib import Path
from backend.services.project_builder import global_structured_project_builder
from backend.schemas.agent_contract import ProjectSpec, ArchitectureSpec
from backend.graph.project_state import ProjectState
from backend.graph.parallel_workflow import assembly_node


@pytest.fixture
def tmp_output_dir(tmp_path):
    out = tmp_path / "generated_projects"
    out.mkdir(parents=True, exist_ok=True)
    yield out
    if out.exists():
        shutil.rmtree(out, ignore_errors=True)


def test_basic_project_generation(tmp_output_dir):
    manifest = {
        "frontend/src/App.jsx": "export default function App() { return <div>TodoApp</div>; }",
        "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()",
        "README.md": "# TodoApp"
    }

    target_dir = global_structured_project_builder.write_project_to_disk("TodoApp", manifest, base_dir=str(tmp_output_dir))

    assert target_dir.exists()
    assert (target_dir / "frontend" / "src" / "App.jsx").exists()
    assert (target_dir / "backend" / "main.py").exists()
    assert (target_dir / "README.md").exists()


def test_nested_directory_creation(tmp_output_dir):
    manifest = {
        "frontend/src/components/layout/Navbar/Navbar.jsx": "// Navbar Component",
        "backend/app/routers/api/v1/auth.py": "# Auth router"
    }

    target_dir = global_structured_project_builder.write_project_to_disk("NestedApp", manifest, base_dir=str(tmp_output_dir))

    assert (target_dir / "frontend" / "src" / "components" / "layout" / "Navbar" / "Navbar.jsx").exists()
    assert (target_dir / "backend" / "app" / "routers" / "api" / "v1" / "auth.py").exists()


def test_file_writing_to_disk(tmp_output_dir):
    content = "SELECT * FROM users;"
    manifest = {"database/schema.sql": content}

    target_dir = global_structured_project_builder.write_project_to_disk("DBSpec", manifest, base_dir=str(tmp_output_dir))

    sql_file = target_dir / "database" / "schema.sql"
    assert sql_file.read_text(encoding="utf-8") == content


def test_path_traversal_prevention(tmp_output_dir):
    manifest = {
        "../../outside.py": "malicious code"
    }

    with pytest.raises(ValueError, match="Path traversal detected"):
        global_structured_project_builder.write_project_to_disk("MaliciousApp", manifest, base_dir=str(tmp_output_dir))


def test_absolute_path_rejection(tmp_output_dir):
    manifest = {
        "/etc/passwd": "malicious"
    }

    with pytest.raises(ValueError, match="Absolute path rejected"):
        global_structured_project_builder.write_project_to_disk("AbsPathApp", manifest, base_dir=str(tmp_output_dir))


def test_existing_project_builder_compatibility():
    assembled = global_structured_project_builder.assemble_real_project(
        project_name="LegacyApp",
        plan_json={"project_name": "LegacyApp"},
        arch_json={"components": ["Navbar"]},
        frontend_code="// Frontend",
        backend_code="# Backend",
        database_code="-- DB",
        testing_code="# Test",
        docs_code="# Docs"
    )

    assert assembled["project_name"] == "LegacyApp"
    assert "manifest" in assembled
    assert len(assembled["manifest"]) > 0


def test_assembly_manifest_generation():
    assembled = global_structured_project_builder.assemble_real_project(
        project_name="ManifestApp",
        plan_json={},
        arch_json={},
        frontend_code="app",
        backend_code="main",
        database_code="sql",
        testing_code="test",
        docs_code="readme"
    )

    assert "manifest" in assembled
    assert "frontend/src/App.jsx" in assembled["manifest"]
    assert "backend/main.py" in assembled["manifest"]


def test_repeated_generation_idempotency(tmp_output_dir):
    manifest1 = {"main.py": "print('v1')"}
    manifest2 = {"main.py": "print('v2')"}

    dir1 = global_structured_project_builder.write_project_to_disk("IdempotentApp", manifest1, base_dir=str(tmp_output_dir))
    assert (dir1 / "main.py").read_text() == "print('v1')"

    dir2 = global_structured_project_builder.write_project_to_disk("IdempotentApp", manifest2, base_dir=str(tmp_output_dir))
    assert dir1 == dir2
    assert (dir2 / "main.py").read_text() == "print('v2')"


@pytest.mark.anyio
async def test_planner_architect_builder_integration(tmp_output_dir, monkeypatch):
    # Integration test simulating Planner -> Architect -> Assembly Node -> Disk Writing
    spec = ProjectSpec(
        project_name="E2ETodoApp",
        frontend="React",
        backend="FastAPI",
        database="PostgreSQL"
    )

    arch = ArchitectureSpec(
        project_name="E2ETodoApp",
        components=["TodoList", "Navbar"],
        routes=["GET /api/todos", "POST /api/todos"],
        models=["User", "Todo"]
    )

    state: ProjectState = {
        "prompt": "Build a Todo application",
        "project_name": "E2ETodoApp",
        "project_spec": spec.model_dump(),
        "architecture": arch.model_dump(),
        "frontend": "// React Todo Component",
        "backend": "# FastAPI Todo Backend",
        "database": "-- PostgreSQL Todo Schema",
        "tests": "# Pytest Todos",
        "documentation": "# E2ETodoApp Readme"
    }

    # Redirect output to tmp_output_dir for clean test isolation
    orig_write = global_structured_project_builder.write_project_to_disk
    def mock_write(proj_name, manifest, base_dir="generated_projects"):
        return orig_write(proj_name, manifest, base_dir=str(tmp_output_dir))

    monkeypatch.setattr(global_structured_project_builder, "write_project_to_disk", mock_write)

    state_update = await assembly_node(state)

    assert "project_path" in state_update
    assert "files" in state_update
    assert "assembly_manifest" in state_update

    written_path = Path(state_update["project_path"])
    assert written_path.exists()
    assert (written_path / "frontend" / "src" / "App.jsx").exists()
    assert (written_path / "backend" / "main.py").exists()
    assert (written_path / "database" / "schema.sql").exists()
