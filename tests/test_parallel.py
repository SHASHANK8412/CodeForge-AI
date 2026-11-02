"""
Frontend, Backend and Database code generation run concurrently in the real pipeline graph.

(Previously this test patched attributes the workflow no longer has, such as
validation_orchestrator. The whole run is covered by tests/test_pipeline_integration.py; this
checks the parallel stage specifically, with the same model-free setup.)
"""
import asyncio
import time

import pytest

from tests.test_pipeline_integration import BACKEND, DATABASE, FRONTEND, _resume, pipeline  # noqa: F401
from backend.graph import parallel_workflow as wf

DELAY = 0.6


@pytest.fixture
def timed_agents(pipeline, monkeypatch):  # noqa: F811 - the imported fixture
    spans = {}

    def slow(name, text):
        async def run_async(*_a, **_k):
            start = time.perf_counter()
            await asyncio.sleep(DELAY)
            spans[name] = (start, time.perf_counter())
            return text
        return run_async

    monkeypatch.setattr(wf.frontend_agent, "run_async", slow("frontend", FRONTEND))
    monkeypatch.setattr(wf.backend_agent, "run_async", slow("backend", BACKEND))
    monkeypatch.setattr(wf.database_agent, "run_async", slow("database", DATABASE))
    return pipeline, spans


def test_parallel_workflow_execution(timed_agents):
    pipeline, spans = timed_agents
    config = {"configurable": {"thread_id": "gen_parallel_1"}}
    asyncio.run(pipeline.graph.ainvoke({"prompt": "Build a notes board", "user_prompt": "Build a notes board",
                                        "project_id": "notes_parallel", "files": {}, "fixes": []}, config=config))
    _resume(pipeline.graph, config, {"approval_status": "approved", "current_step": "dispatch_parallel"})

    assert set(spans) == {"frontend", "backend", "database"}
    first_start = min(s for s, _ in spans.values())
    last_end = max(e for _, e in spans.values())
    assert last_end - first_start < 2 * DELAY, f"agents ran one after another: {spans}"
    # All three outputs reached assembly.
    files = pipeline.graph.get_state(config).values["files"]
    assert {"backend/main.py", "frontend/src/App.jsx", "database/schema.sql"} <= set(files)
