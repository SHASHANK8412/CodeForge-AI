import pytest
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path
from backend.graph import parallel_workflow


class MockAgent:
    def __init__(self, name: str, key: str | None = None):
        self.name = name
        self.key = key

    async def run_async(self, *args, **kwargs) -> str | dict[str, str]:
        if self.key:
            return {self.key: f"{self.name} output"}
        return f"{self.name} output"


@pytest.mark.anyio
async def test_parallel_workflow_execution():
    # Setup mocks for parallel workflow nodes
    parallel_workflow.planner = MockAgent("Planner")
    parallel_workflow.architect = MockAgent("Architect")
    parallel_workflow.frontend_agent = MockAgent("Frontend")
    parallel_workflow.backend_agent = MockAgent("Backend", "backend")
    parallel_workflow.database_agent = MockAgent("Database", "database")
    parallel_workflow.testing_agent = MockAgent("Testing")
    parallel_workflow.documentation_agent = MockAgent("Documentation", "documentation")
    parallel_workflow.reviewer_agent = MockAgent("Reviewer")

    # Save original globals to restore them
    orig_generator = parallel_workflow.project_generator
    orig_healer = parallel_workflow.self_heal_orchestrator

    # Mock new generators and healing services
    parallel_workflow.project_generator = MagicMock()
    parallel_workflow.project_generator.generate_project_structure.return_value = (Path("/tmp"), None)
    parallel_workflow.project_generator.zip_service = MagicMock()

    parallel_workflow.self_heal_orchestrator = AsyncMock()
    parallel_workflow.self_heal_orchestrator.execute_self_heal_pipeline.return_value = ([], {}, {}, "Mock Report")

    try:
        result = await parallel_workflow.parallel_graph.ainvoke(
            {
                "prompt": "Build an AI Resume Analyzer",
                "user_prompt": "Build an AI Resume Analyzer",
            }
        )
    finally:
        parallel_workflow.project_generator = orig_generator
        parallel_workflow.self_heal_orchestrator = orig_healer

    assert result["plan"] == "Planner output"
    assert result["architecture"] == "Architect output"
    assert result["frontend"] == "Frontend output"
    assert result["backend"] == "Backend output"
    assert result["database"] == "Database output"
    assert result["tests"] == "Testing output"
    assert result["documentation"] == "Documentation output"
    assert result["review"] == "Reviewer output"
    assert result["current_step"] == "export"
