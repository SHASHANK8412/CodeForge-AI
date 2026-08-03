"""
Unit Tests for AIForge Evaluation Engine
========================================
Tests dataset loading, schema validation, routing evaluation, quality scoring,
baseline comparison, regression detection, improvement detection, and Formula 1 critical test.
"""

import sys
import unittest
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.evaluation.models import GoldenTestCase, BenchmarkReport, TestCaseResult
from backend.evaluation.runner import EvaluationRunner
from backend.evaluation.evaluators.routing_evaluator import global_routing_evaluator
from backend.evaluation.evaluators.quality_evaluator import global_quality_evaluator
from backend.evaluation.regression import global_regression_analyzer


class TestEvaluationEngine(unittest.TestCase):

    def setUp(self):
        self.runner = EvaluationRunner()

    def test_golden_dataset_contains_100_items(self):
        dataset = self.runner.load_dataset()
        self.assertGreaterEqual(len(dataset), 100, f"Expected at least 100 golden prompts, found {len(dataset)}")
        self.assertTrue(all(isinstance(c, GoldenTestCase) for c in dataset))

    def test_category_distribution(self):
        dataset = self.runner.load_dataset()
        categories = [c.category for c in dataset]
        self.assertIn("explanation", categories)
        self.assertIn("coding", categories)
        self.assertIn("debugging", categories)
        self.assertIn("general_qa", categories)
        self.assertIn("rag", categories)
        self.assertIn("resume", categories)
        self.assertIn("project", categories)
        self.assertIn("ambiguous", categories)

    def test_flagship_formula_1_test_case_exists(self):
        dataset = self.runner.load_dataset()
        f1_case = next((c for c in dataset if c.id == "EXP_FORMULA1"), None)
        self.assertIsNotNone(f1_case, "EXP_FORMULA1 flagship test case missing!")
        self.assertEqual(f1_case.expected_intent, "EXPLANATION")
        self.assertEqual(f1_case.expected_agent, "ExplanationAgent")
        self.assertTrue(f1_case.critical)
        self.assertIn("def solve(", f1_case.forbidden_elements)

    def test_routing_evaluator(self):
        case = GoldenTestCase(
            id="TEST_001",
            category="explanation",
            prompt="Explain Formula 1",
            expected_intent="EXPLANATION",
            expected_agent="ExplanationAgent",
            expected_profile="EXPLANATION"
        )
        res = global_routing_evaluator.evaluate_routing(case)
        self.assertTrue(res["intent_pass"])
        self.assertTrue(res["agent_pass"])
        self.assertTrue(res["overall_routing_pass"])

    def test_quality_evaluator_required_and_forbidden_elements(self):
        case = GoldenTestCase(
            id="TEST_002",
            category="explanation",
            prompt="Explain Formula 1",
            expected_intent="EXPLANATION",
            expected_agent="ExplanationAgent",
            required_elements=["Formula 1", "racing"],
            forbidden_elements=["def solve("]
        )
        # Good response
        good_resp = "Formula 1 is auto racing."
        good_qual = global_quality_evaluator.evaluate_quality(case, good_resp, "EXPLANATION", "ExplanationAgent")
        self.assertTrue(good_qual["required_elements_pass"])
        self.assertTrue(good_qual["forbidden_elements_pass"])
        self.assertTrue(good_qual["overall_quality_pass"])

        # Bad response with forbidden string
        bad_resp = "Formula 1 auto racing. def solve(): pass"
        bad_qual = global_quality_evaluator.evaluate_quality(case, bad_resp, "EXPLANATION", "ExplanationAgent")
        self.assertFalse(bad_qual["forbidden_elements_pass"])
        self.assertFalse(bad_qual["overall_quality_pass"])

    def test_simulated_regression_detection(self):
        base_report = BenchmarkReport(
            benchmark_id="base",
            timestamp="2026_08_03_100000",
            mode="fast",
            total_tests=10,
            passed_tests=10,
            failed_tests=0,
            overall_pass_rate_pct=100.0,
            routing_accuracy_pct=100.0,
            agent_accuracy_pct=100.0,
            profile_accuracy_pct=100.0,
            average_quality_score=95.0,
            critical_tests_count=2,
            critical_tests_passed=2,
            critical_tests_pass_pct=100.0,
            regeneration_rate_pct=0.0,
            avg_latency_ms=10.0,
            p50_latency_ms=10.0,
            p95_latency_ms=15.0,
            results=[]
        )

        curr_report = base_report.model_copy(deep=True)
        curr_report.average_quality_score = 88.0  # -7 point drop

        reg = global_regression_analyzer.compare(curr_report, base_report)
        self.assertTrue(reg.has_regression)
        self.assertIn("REGRESSION DETECTED", reg.summary_message)

    def test_simulated_improvement_detection(self):
        base_tc = TestCaseResult(
            test_id="COD_001",
            category="coding",
            prompt="Write code",
            expected_intent="CODING",
            actual_intent="CODING",
            expected_agent="CodingAgent",
            actual_agent="CodingAgent",
            expected_profile="CODING",
            actual_profile="CODING",
            routing_pass=True,
            agent_pass=True,
            profile_pass=True,
            quality_score=75.0,
            contract_pass=True,
            required_elements_pass=True,
            forbidden_elements_pass=True,
            language_match_pass=True,
            rag_facts_pass=True,
            latency_ms=5.0,
            regenerated=False,
            attempts=1,
            critical=False,
            overall_pass=True
        )

        base_report = BenchmarkReport(
            benchmark_id="base",
            timestamp="2026_08_03_100000",
            mode="fast",
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            overall_pass_rate_pct=100.0,
            routing_accuracy_pct=100.0,
            agent_accuracy_pct=100.0,
            profile_accuracy_pct=100.0,
            average_quality_score=75.0,
            critical_tests_count=0,
            critical_tests_passed=0,
            critical_tests_pass_pct=100.0,
            regeneration_rate_pct=0.0,
            avg_latency_ms=5.0,
            p50_latency_ms=5.0,
            p95_latency_ms=5.0,
            results=[base_tc]
        )

        curr_tc = base_tc.model_copy(deep=True)
        curr_tc.quality_score = 95.0  # +20 point improvement

        curr_report = base_report.model_copy(deep=True)
        curr_report.average_quality_score = 95.0
        curr_report.results = [curr_tc]

        reg = global_regression_analyzer.compare(curr_report, base_report)
        self.assertFalse(reg.has_regression)
        self.assertGreater(len(reg.improvements_list), 0)

    def test_mock_evaluation_runner_mode(self):
        report = self.runner.run_evaluation(mode="mock", category_filter="explanation")
        self.assertGreater(report.total_tests, 0)
        self.assertEqual(report.mode, "mock")
        self.assertGreaterEqual(report.overall_pass_rate_pct, 90.0)


if __name__ == "__main__":
    unittest.main()
