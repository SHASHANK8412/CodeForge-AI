"""
AIForge Day 102 Test Suite: Continuous Benchmarking & Knowledge Graph
======================================================================
"""

import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from backend.learning.benchmark import global_benchmark_engine
from backend.learning.knowledge_graph import global_knowledge_graph_engine
from backend.learning.evolution_engine import global_evolution_engine


class TestDay102BenchmarkAndEvolution(unittest.TestCase):

    def test_01_benchmark_project_metrics(self):
        res = global_benchmark_engine.benchmark_project("E-Commerce Portal")
        self.assertTrue(res["benchmark_passed"])
        self.assertIn("improvement_pct", res)
        self.assertEqual(res["complexity_reduction"], "18 → 7")
        print("✓ Benchmark project metrics test passed")

    def test_02_system_knowledge_graph(self):
        graph = global_knowledge_graph_engine.build_system_knowledge_graph()
        self.assertEqual(graph["total_nodes"], 6)
        self.assertEqual(graph["total_edges"], 5)
        print("✓ System knowledge graph test passed")

    def test_03_autonomous_refactoring_suggestions(self):
        loop = global_evolution_engine.generate_evolution_loop("SaaS Platform")
        self.assertEqual(loop["evolution_cycle_status"], "COMPLETED")
        self.assertGreater(len(loop["autonomous_refactoring_suggestions"]), 0)
        print("✓ Autonomous refactoring suggestions test passed")


def main():
    print("\n" + "="*60)
    print(" Running Day 102 Benchmark & Evolution Tests...")
    print("="*60 + "\n")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDay102BenchmarkAndEvolution)
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
