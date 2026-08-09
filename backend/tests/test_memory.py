"""
Unit tests for Day 44 MemoryIndexer
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.services.memory_indexer import MemoryIndexer


class TestMemoryIndexer(unittest.TestCase):

    def setUp(self):
        self.indexer = MemoryIndexer()

    def test_project_indexing(self):
        knowledge = {
            "ui_components": [{"file": "App.jsx", "code": "React code"}],
            "error_resolution_pairs": [{"error": "Missing module", "solution": "pip install"}]
        }
        rec = self.indexer.index_project(
            project_id="test_idx_01",
            prompt="Build blog app",
            knowledge=knowledge,
            quality_score=95.0
        )
        self.assertEqual(rec["project_id"], "test_idx_01")
        self.assertIn("blog", rec["tags"])


if __name__ == "__main__":
    unittest.main()
