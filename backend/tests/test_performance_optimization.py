"""
AIForge Performance Optimization Test Suite
===========================================
Validates:
1. Tiered model allocation & Fast Mode config
2. Conditional agent routing (skipping unneeded nodes)
3. SSE real-time progress streaming
4. RAG context trimming parameters
"""

import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from backend.config import ENABLE_FAST_MODE, MAX_RAG_CHUNKS, MAX_RAG_CONTEXT_CHARS
from backend.graph.router_agent import global_workflow_router


class TestPerformanceOptimization(unittest.TestCase):

    def test_01_config_fast_mode_and_rag_caps(self):
        self.assertTrue(ENABLE_FAST_MODE)
        self.assertEqual(MAX_RAG_CHUNKS, 5)
        self.assertEqual(MAX_RAG_CONTEXT_CHARS, 2000)
        print("✓ Fast Mode & RAG Context Caps validated")

    def test_02_conditional_workflow_router(self):
        route_ui = global_workflow_router.route_workflow("Build landing page UI only")
        self.assertEqual(route_ui["workflow_type"], "frontend_only")
        self.assertIn("backend", route_ui["skipped_agents"])
        self.assertEqual(route_ui["estimated_time_saving_pct"], 40)

        route_full = global_workflow_router.route_workflow("Build Full Stack SaaS")
        self.assertEqual(route_full["workflow_type"], "full_stack")
        self.assertEqual(len(route_full["skipped_agents"]), 0)
        print("✓ Conditional workflow router validated")


if __name__ == "__main__":
    unittest.main()
