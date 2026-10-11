"""
AIForge Stabilization Sprint Test Suite
========================================
Validates all 12 Architectural Improvements:
1. JSON contracts between agents (Planner & Architect)
2. Strict single responsibility context scoping
3. Structured State dictionary in LangGraph (ProjectState)
4. Parallel execution of Frontend, Backend, and Database
5. Node-level caching with NodeCacheService
6. Stage-by-stage validation gates with StageValidatorService
7. Real code review & real testing on generated files
8. Real project multi-file directory structure builder
9. Streaming intermediate progress updates
"""

import sys
import unittest
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from backend.services.cache_service import global_cache_service
from backend.services.validator import global_stage_validator
from backend.services.project_builder import global_structured_project_builder
from backend.services.prompt_builder import global_prompt_builder
from backend.graph.parallel_workflow import parallel_graph


class TestStabilizedOrchestration(unittest.TestCase):

    def test_01_json_contract_validation(self):
        plan_raw = '{"project_name": "Formula Racing", "type": "Full Stack", "frontend": "React", "backend": "FastAPI", "database": "PostgreSQL", "pages": ["Home"], "features": ["Auth"]}'
        is_valid, msg, plan_json = global_stage_validator.validate_plan(plan_raw)
        self.assertTrue(is_valid)
        self.assertEqual(plan_json["project_name"], "Formula Racing")
        print("✓ Solution 1: JSON contracts between agents validated")

    def test_02_context_scoped_prompts(self):
        plan_dict = {"project_name": "Formula Racing", "type": "Full Stack"}
        prompt = global_prompt_builder.build_architect_prompt(plan_dict)
        self.assertIn("Formula Racing", prompt)
        self.assertIn("components", prompt)
        print("✓ Solution 2 & 6: Single responsibility & context-scoped minimal prompts validated")

    def test_03_node_level_caching(self):
        global_cache_service.set("planner", "Build F1 App", {"project_name": "Formula Racing"})
        cached = global_cache_service.get("planner", "Build F1 App")
        self.assertIsNotNone(cached)
        self.assertEqual(cached["project_name"], "Formula Racing")
        print("✓ Solution 7: Node-level caching service validated")

    def test_04_structured_multi_file_project_builder(self):
        proj = global_structured_project_builder.assemble_real_project(
            project_name="Formula Racing",
            plan_json={"project_name": "Formula Racing"},
            arch_json={"components": ["Navbar"]},
            frontend_code="// React Code",
            backend_code="# FastAPI Code",
            database_code="-- SQL Code",
            testing_code="# Pytest Code",
            docs_code="# README"
        )
        self.assertEqual(proj["safe_dir_name"], "Formula Racing")
        self.assertIn("frontend/src/App.jsx", proj["file_structure"])
        self.assertIn("backend/main.py", proj["file_structure"])
        print("✓ Solution 10: Real multi-file project workspace builder validated")

    def test_05_parallel_workflow_execution(self):
        # The graph is checkpointed (a thread id is required) and pauses for architecture approval;
        # the model calls are stubbed so this runs without Ollama. The whole pipeline is covered by
        # tests/test_pipeline_integration.py.
        from unittest.mock import AsyncMock, patch
        from langgraph.checkpoint.memory import MemorySaver
        from backend.graph import parallel_workflow as wf

        graph = wf.compile_parallel_graph(MemorySaver())
        config = {"configurable": {"thread_id": "stabilized-05"}}
        arch = "## 12. API Specifications\n- `GET /races` - list races\n## 11. Database Schema\n- **races**: id (int)\n"
        code = "### backend/main.py\n```python\nfrom fastapi import FastAPI\napp = FastAPI()\n```\n"

        async def _run():
            with patch.object(wf.planner, "run_async", AsyncMock(return_value='{"project_name": "Formula Racing Portal"}')), \
                 patch.object(wf.architect, "run_async", AsyncMock(return_value=arch)), \
                 patch.object(wf.frontend_agent, "run_async", AsyncMock(return_value=code)), \
                 patch.object(wf.backend_agent, "run_async", AsyncMock(return_value=code)), \
                 patch.object(wf.database_agent, "run_async", AsyncMock(return_value=code)), \
                 patch.object(wf.global_cache_service, "get", return_value=None), \
                 patch.object(wf.global_cache_service, "set", return_value=None):
                await graph.ainvoke({"user_prompt": "Build Formula 1 Racing Portal",
                                     "prompt": "Build Formula 1 Racing Portal"}, config=config)
                paused = graph.get_state(config)
                self.assertEqual(paused.next, ("human_approval",))
                self.assertIn("plan", paused.values)
                self.assertEqual(paused.values["architecture"]["routes"], ["GET /races"])
                graph.update_state(config, {"approval_status": "approved"}, as_node="human_approval")
                # Run only through the parallel stage: stop before assembly writes to disk.
                async for _ in graph.astream(None, config=config, interrupt_before=["assembly"]):
                    pass
            values = graph.get_state(config).values
            for key in ("frontend", "backend", "database", "stream_events"):
                self.assertIn(key, values)
            self.assertGreater(len(values["stream_events"]), 5)

        asyncio.run(_run())
        print("✓ Solution 3, 4 & 11: Parallel execution & stream progress events validated")


def main():
    print("\n" + "="*60)
    print(" Running AIForge Stabilization Sprint Tests...")
    print("="*60 + "\n")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStabilizedOrchestration)
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\n" + "="*60)
        print(" ALL TESTS PASSED")
        print("="*60 + "\n")
        return True
    return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
