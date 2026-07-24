"""
AIForge Day 96 & 97 Test Suite: Semantic Similarity & Retrieval
"""

import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from backend.learning.similarity import global_semantic_similarity_engine


class TestSimilaritySearch(unittest.TestCase):

    def test_01_find_similar_ecommerce_project(self):
        results = global_semantic_similarity_engine.find_similar_projects("Build an Ecommerce Store with Stripe", top_k=2)
        self.assertGreater(len(results), 0)
        self.assertIn("similarity_score_pct", results[0])
        self.assertGreater(results[0]["similarity_score_pct"], 80.0)
        self.assertIn("reusable_components", results[0])
        print("✓ Semantic vector similarity search test passed")


if __name__ == "__main__":
    unittest.main()
