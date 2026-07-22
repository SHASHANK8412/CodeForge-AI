import asyncio
import pytest
from fastapi.testclient import TestClient

from backend.graph import project_workflow
from backend.main import app


class MockAgent:
    def __init__(self, name: str, key: str | None = None):
        self.name = name
        self.key = key

    async def run_async(self, *args, **kwargs) -> str | dict[str, str]:
        print(f"{self.name} started...")
        print(f"{self.name} completed...")
        if self.key:
            return {self.key: f"{self.name} output"}
        return f"{self.name} output"


@pytest.mark.anyio
async def test_entire_pipeline():
    # Setup mocks for all agents
    project_workflow.planner = MockAgent("Planner")
    project_workflow.architect = MockAgent("Architect")
    project_workflow.frontend_agent = MockAgent("Frontend")
    project_workflow.backend_agent = MockAgent("Backend", "backend")
    project_workflow.database_agent = MockAgent("Database", "database")
    project_workflow.reviewer_agent = MockAgent("Reviewer")
    project_workflow.testing_agent = MockAgent("Testing")
    project_workflow.documentation_agent = MockAgent("Documentation", "documentation")

    # Run the graph
    result = await project_workflow.project_graph.ainvoke(
        {
            "prompt": "Build an AI Resume Analyzer",
            "user_prompt": "Build an AI Resume Analyzer",
        }
    )

    # Print workflow completion log
    print("Workflow completed successfully.")

    print("\n========== FINAL STATE ==========\n")
    for key, value in result.items():
        print(f"{key}:")
        print(value)
        print("-" * 60)

    # Validate state values are populated
    assert result.get("plan") == "Planner output"
    assert result.get("architecture") == "Architect output"
    assert result.get("frontend") == "Frontend output"
    assert result.get("backend") == "Backend output"
    assert result.get("database") == "Database output"
    assert result.get("review") == "Reviewer output"
    assert result.get("tests") == "Testing output"
    assert result.get("documentation") == "Documentation output"
    assert result.get("current_step") == "documentation"


def test_generate_endpoint():
    # Setup mocks for parallel_workflow agents since the endpoint now invokes the parallel graph
    from backend.graph import parallel_workflow
    parallel_workflow.planner = MockAgent("Planner")
    parallel_workflow.architect = MockAgent("Architect")
    parallel_workflow.frontend_agent = MockAgent("Frontend")
    parallel_workflow.backend_agent = MockAgent("Backend", "backend")
    parallel_workflow.database_agent = MockAgent("Database", "database")
    parallel_workflow.reviewer_agent = MockAgent("Reviewer")
    parallel_workflow.testing_agent = MockAgent("Testing")
    parallel_workflow.documentation_agent = MockAgent("Documentation", "documentation")

    from backend.validation.models import ValidationReport, QualityScore
    from unittest.mock import AsyncMock
    parallel_workflow.validation_orchestrator.execute_validation_pipeline = AsyncMock(return_value=(
        ValidationReport(
            timestamp="2026-07-19T13:00:00Z",
            project_name="Build an AI Resume Analyzer",
            results=[],
            quality=QualityScore(overall_score=95.0, grade="A", ready_for_export=True),
            summary={}
        ),
        True
    ))

    client = TestClient(app)
    response = client.post("/generate", json={"prompt": "Build an AI Resume Analyzer"})
    assert response.status_code == 200

    data = response.json()
    print("\n========== API RESPONSE KEYS ==========\n")
    for key, val in data.items():
        print(f" - {key}: {type(val)} (length: {len(str(val))})")

    assert data["plan"] == "Planner output"
    assert data["architecture"] == "Architect output"
    assert data["frontend"] == "Frontend output"
    assert data["backend"] == "Backend output"
    assert data["database"] == "Database output"
    assert data["review"] == "Reviewer output"
    assert data["tests"] == "Testing output"
    assert data["documentation"].startswith("Documentation output")

    # Legacy compatibility checks
    assert data["generated_code"] == "Backend output"
    assert data["reviewed_code"] == "Reviewer output"
    assert data["testing_report"] == "Testing output"
    assert data["explanation"].startswith("Documentation output")
