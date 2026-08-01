"""
PyTest Unit & Integration Test Suite: AIForge V2 Next-Gen Enhancements
========================================================================
Verifies:
1. AST Code Analyzer Symbol Extraction
2. LSP Diagnostics & Symbol Definition Lookup
3. LangGraph State Checkpointing Save & Restore
4. Redis Shared Cache Manager
5. Static Analysis Quality Scanner (Bandit, Semgrep, Ruff, MyPy)
6. Incremental Module Generation Engine
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.analysis.ast_analyzer import ASTCodeAnalyzer
from backend.analysis.lsp_engine import LSPEngine
from backend.graph.checkpoint_engine import LangGraphCheckpointEngine
from backend.utils.redis_cache import RedisSharedCache
from backend.quality.static_analysis import StaticAnalysisEngine
from backend.generators.incremental_generator import IncrementalProjectGenerator
from backend.memory.project_memory import ProjectMemoryStore


class TestNextGenFeatures(unittest.TestCase):

    def test_ast_code_analyzer(self):
        analyzer = ASTCodeAnalyzer()
        code = "import os\nclass User:\n    pass\ndef login(email: str) -> bool:\n    return True"
        res = analyzer.analyze_python_code("app/test.py", code)
        self.assertTrue(res["valid_syntax"])
        self.assertEqual(len(res["classes"]), 1)
        self.assertEqual(len(res["functions"]), 1)
        self.assertEqual(res["classes"][0]["name"], "User")

    def test_lsp_engine_symbol_lookup(self):
        lsp = LSPEngine()
        files = {
            "app/models.py": "class User:\n    pass",
            "app/auth.py": "def login(): pass"
        }
        idx = lsp.index_codebase(files)
        self.assertGreaterEqual(idx["symbol_count"], 2)
        defn = lsp.find_definition("User")
        self.assertIsNotNone(defn)
        self.assertEqual(defn["kind"], "class")

    def test_checkpoint_engine(self):
        ckpt = LangGraphCheckpointEngine()
        data = {"stage": "planner", "plan": {"name": "Test"}}
        file_path = ckpt.save_checkpoint("session_123", "planner", data)
        self.assertTrue(file_path.endswith(".json"))
        loaded = ckpt.load_latest_checkpoint("session_123")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["stage"], "planner")

    def test_redis_shared_cache(self):
        cache = RedisSharedCache()
        cache.set("test_key", "cached_val")
        self.assertEqual(cache.get("test_key"), "cached_val")

    def test_static_analysis_engine(self):
        sa = StaticAnalysisEngine()
        files = {
            "app/auth.py": "import os\ndef login(email):\n    try:\n        pass\n    except:\n        pass"
        }
        rep = sa.run_static_analysis(files)
        self.assertGreaterEqual(rep["static_analysis_score"], 90.0)
        self.assertGreaterEqual(rep["total_findings"], 1)

    def test_incremental_generator(self):
        gen = IncrementalProjectGenerator()
        mem = ProjectMemoryStore("Incremental Test")
        out_files = gen.generate_modules_incrementally("Incremental Test", mem)
        self.assertIn("backend/main.py", out_files)
        self.assertIn("frontend/src/App.jsx", out_files)
        self.assertIn("database/schema.sql", out_files)


if __name__ == "__main__":
    unittest.main()
