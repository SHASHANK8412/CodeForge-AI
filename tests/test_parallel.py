import pytest
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

    result = await parallel_workflow.parallel_graph.ainvoke(
        {
            "prompt": "Build an AI Resume Analyzer",
            "user_prompt": "Build an AI Resume Analyzer",
        }
    )

    assert result["plan"] == "Planner output"
    assert result["architecture"] == "Architect output"
    assert result["frontend"] == "Frontend output"
    assert result["backend"] == "Backend output"
    assert result["database"] == "Database output"
    assert result["tests"] == "Testing output"
    assert result["documentation"] == "Documentation output"
    assert result["review"] == "Reviewer output"
    assert result["current_step"] == "reviewer"
