"""
AIForge Day 96 & 97 Test Suite: AI Reflection & Quality Score Report
"""

import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from backend.learning.reflection import global_ai_reflection_engine


class TestAIReflection(unittest.TestCase):

    def test_01_generate_reflection_report(self):
        reflection = global_ai_reflection_engine.generate_reflection(
            project_name="Ecommerce Microservice",
            architecture_score=95.0,
            code_quality_score=94.0,
            security_score=98.0,
            performance_score=92.0,
            testing_score=97.0,
            documentation_score=96.0
        )
        self.assertEqual(reflection["overall_score"], 95.6)
        self.assertIn("formatted_report", reflection)
        self.assertIn("Overall:      95.6%", reflection["formatted_report"])
        self.assertGreater(len(reflection["what_went_well"]), 0)
        print("✓ AI Reflection & Quality Score Report test passed")


if __name__ == "__main__":
    unittest.main()
