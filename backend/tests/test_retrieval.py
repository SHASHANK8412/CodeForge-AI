"""
Unit tests for Day 44 MemoryRetriever
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
from backend.services.memory_indexer import MemoryIndexer
from backend.services.memory_retriever import MemoryRetriever


class TestMemoryRetriever(unittest.TestCase):

    def setUp(self):
        self.indexer = MemoryIndexer()
        self.retriever = MemoryRetriever()

        # Seed indexed project
        self.indexer.index_project(
            project_id="test_ret_01",
            prompt="Create e-commerce dashboard",
            knowledge={"ui_components": [{"name": "DashboardCard"}]},
            quality_score=97.0
        )

    def test_search_and_context_retrieval(self):
        similar = self.retriever.search_similar_projects("e-commerce app", top_k=3)
        self.assertGreaterEqual(len(similar), 1)

        ctx = self.retriever.retrieve_context_for_prompt("Build e-commerce store")
        self.assertIn("context_prompt_snippet", ctx)
        self.assertGreaterEqual(ctx["similar_projects_count"], 1)


if __name__ == "__main__":
    unittest.main()
