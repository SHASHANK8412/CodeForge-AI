import shutil
import pytest
from pathlib import Path
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.workflow.project_builder import build_project, GENERATED_PROJECTS_DIR
from backend.graph import parallel_workflow


class MockAgent:
    def __init__(self, name: str, key: str | None = None):
        self.name = name
        self.key = key

    async def run_async(self, *args, **kwargs) -> str | dict[str, str]:
        # Generate some mock file structures in backend output
        if self.key == "backend":
            return {
                "backend": """
# filepath: backend/main.py
from fastapi import FastAPI
app = FastAPI()
"""
            }
        elif self.key == "frontend":
            return {
                "frontend": """
// filepath: frontend/src/App.jsx
export default function App() { return <div>AIForge Application</div> }
"""
            }
        elif self.key:
            return {self.key: f"{self.name} output"}
        return f"{self.name} output"


def test_project_assembly_and_zip():
    # Setup mock data state
    mock_state = {
        "plan": "Planner plan",
        "architecture": "Architect design",
        "frontend": "```jsx\n// filepath: frontend/src/App.jsx\nexport default function App() {}\n```",
        "backend": "```python\n# filepath: backend/main.py\nprint('hello')\n```",
        "database": "CREATE TABLE users (id INT);",
        "tests": "def test_something(): pass",
        "documentation": "README docs content",
    }

    project_name = "Test-Dummy-Project"
    safe_name = "Test-Dummy-Project"
    project_dir = GENERATED_PROJECTS_DIR / safe_name
    zip_path = GENERATED_PROJECTS_DIR / f"{safe_name}.zip"

    # Clean up first
    if project_dir.exists():
        shutil.rmtree(project_dir)
    if zip_path.exists():
        zip_path.unlink()

    # Build
    build_project(project_name, mock_state)

    # Verify directory and files
    assert project_dir.exists()
    assert (project_dir / "frontend/src/App.jsx").exists()
    assert (project_dir / "backend/main.py").exists()
    assert (project_dir / "database/schema.sql").exists()
    assert (project_dir / "tests/test_app.py").exists()
    assert (project_dir / "README.md").exists()
    assert (project_dir / "project.json").exists()

    # Verify ZIP file exists
    assert zip_path.exists()

    # Verify metadata JSON contents
    with open(project_dir / "project.json", "r") as f:
        metadata = json.load(f)
    assert metadata["project_name"] == project_name
    assert metadata["framework"] == "React + FastAPI"

    # Clean up
    shutil.rmtree(project_dir)
    zip_path.unlink()


def test_api_generation_and_download():
    # Mock pipeline agents so it is instant
    parallel_workflow.planner = MockAgent("Planner")
    parallel_workflow.architect = MockAgent("Architect")
    parallel_workflow.frontend_agent = MockAgent("Frontend")
    parallel_workflow.backend_agent = MockAgent("Backend", "backend")
    parallel_workflow.database_agent = MockAgent("Database", "database")
    parallel_workflow.reviewer_agent = MockAgent("Reviewer")
    parallel_workflow.testing_agent = MockAgent("Testing")
    parallel_workflow.documentation_agent = MockAgent("Documentation", "documentation")

    orig_healer = parallel_workflow.self_heal_orchestrator

    from backend.validation.models import ValidationReport, QualityScore
    parallel_workflow.validation_orchestrator.execute_validation_pipeline = AsyncMock(return_value=(
        ValidationReport(
            timestamp="2026-07-19T13:00:00Z",
            project_name="HMS-System",
            results=[],
            quality=QualityScore(overall_score=95.0, grade="A", ready_for_export=True),
            summary={}
        ),
        True
    ))

    from backend.graph.reflection_node import reflection_agent
    reflection_agent.reflect_on_project = AsyncMock(return_value={
        "strengths": ["Clean structure"],
        "weaknesses": ["None"],
        "recommendations": [],
        "lessons": [],
        "reflection_score": 95
    })

    # Save original validation and reflection methods
    orig_val = parallel_workflow.validation_orchestrator.execute_validation_pipeline
    orig_ref = reflection_agent.reflect_on_project

    # Mock self-healing to return immediately
    parallel_workflow.self_heal_orchestrator = AsyncMock()
    parallel_workflow.self_heal_orchestrator.execute_self_heal_pipeline.return_value = (
        [], {"passed": 2, "failed": 0}, {"overall": 9.5}, "Mock report content"
    )

    project_name = "HMS-System"
    safe_name = "HMS-System"
    project_dir = GENERATED_PROJECTS_DIR / safe_name
    zip_path = GENERATED_PROJECTS_DIR / f"{safe_name}.zip"

    # Clean up
    if project_dir.exists():
        shutil.rmtree(project_dir)
    if zip_path.exists():
        zip_path.unlink()

    try:
        client = TestClient(app)

        # Generate Project API
        response = client.post("/generate-project", json={"prompt": project_name})
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["project_name"] == project_name
        assert "location" in data

        # Verify files created on disk
        assert project_dir.exists()
        assert zip_path.exists()

        # Download Project ZIP API
        download_response = client.get(f"/download-project/{project_name}")
        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "application/zip"
    finally:
        parallel_workflow.self_heal_orchestrator = orig_healer
        parallel_workflow.validation_orchestrator.execute_validation_pipeline = orig_val
        reflection_agent.reflect_on_project = orig_ref
        # Clean up
        if project_dir.exists():
            shutil.rmtree(project_dir)
        if zip_path.exists():
            zip_path.unlink()


import json
