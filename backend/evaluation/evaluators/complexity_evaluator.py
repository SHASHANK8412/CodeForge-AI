"""
AIForge Task Complexity & Strategy Evaluator
===========================================
Evaluates Complexity Classification Accuracy, Strategy Selection Accuracy,
Planning Overuse Rate, Planning Underuse Rate, and Strategy Latency.
"""

from typing import Dict, Any, List
from backend.reasoning.complexity_analyzer import global_complexity_analyzer
from backend.reasoning.strategy_selector import global_strategy_selector


class ComplexityEvaluator:
    """
    Evaluates complexity analyzer and strategy selector against golden test cases.
    """

    def evaluate(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = 0
        correct_complexity = 0
        correct_strategy = 0

        simple_count = 0
        planning_overuse_count = 0  # Simple prompt incorrectly triggering PLANNED/WORKFLOW

        complex_count = 0
        planning_underuse_count = 0  # Complex/Workflow prompt incorrectly using DIRECT/STANDARD

        workflow_total = 0
        workflow_correct = 0

        for tc in test_cases:
            prompt = tc["prompt"]
            intent = tc.get("expected_intent", "GENERAL_QA")

            exp_complexity = tc.get("expected_complexity")
            exp_strategy = tc.get("expected_strategy")

            if not exp_complexity or not exp_strategy:
                continue

            total += 1

            c_res = global_complexity_analyzer.analyze(prompt, intent)
            actual_complexity = c_res.level.value
            actual_strategy = global_strategy_selector.select(c_res, intent).value

            if actual_complexity == exp_complexity:
                correct_complexity += 1

            if actual_strategy == exp_strategy:
                correct_strategy += 1

            # Planning Overuse Check (TRIVIAL / SIMPLE expected)
            if exp_complexity in ["TRIVIAL", "SIMPLE"]:
                simple_count += 1
                if actual_strategy in ["PLANNED", "WORKFLOW"]:
                    planning_overuse_count += 1

            # Planning Underuse Check (COMPLEX / WORKFLOW expected)
            if exp_complexity in ["COMPLEX", "WORKFLOW"]:
                complex_count += 1
                if actual_strategy in ["DIRECT", "STANDARD"]:
                    planning_underuse_count += 1

            # Workflow Activation Check
            if exp_strategy == "WORKFLOW":
                workflow_total += 1
                if actual_strategy == "WORKFLOW":
                    workflow_correct += 1

        comp_acc = (correct_complexity / total * 100.0) if total > 0 else 100.0
        strat_acc = (correct_strategy / total * 100.0) if total > 0 else 100.0
        overuse_rate = (planning_overuse_count / simple_count * 100.0) if simple_count > 0 else 0.0
        underuse_rate = (planning_underuse_count / complex_count * 100.0) if complex_count > 0 else 0.0
        workflow_acc = (workflow_correct / workflow_total * 100.0) if workflow_total > 0 else 100.0

        return {
            "total_tested": total,
            "complexity_accuracy": round(comp_acc, 2),
            "strategy_accuracy": round(strat_acc, 2),
            "planning_overuse_rate": round(overuse_rate, 2),
            "planning_underuse_rate": round(underuse_rate, 2),
            "workflow_activation_accuracy": round(workflow_acc, 2)
        }


global_complexity_evaluator = ComplexityEvaluator()
