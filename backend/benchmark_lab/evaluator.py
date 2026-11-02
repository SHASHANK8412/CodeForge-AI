"""
AIForge Benchmark Lab — Objective Evaluator
===========================================
Calculates deterministic evaluation metrics from physical execution results,
AST analysis, requirement adherence, test pass rates, and performance timings.
"""

import ast
import re
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from backend.benchmark_lab.models import (
    BenchmarkTask,
    TaskMetricScores,
)

_logger = logging.getLogger("aiforge.benchmark_lab.evaluator")


class ObjectiveEvaluator:
    """
    Computes objective, deterministic scores across correctness, quality,
    adherence, reliability, and efficiency.
    """

    @staticmethod
    def parse_pytest_counts(stdout: str, stderr: str) -> tuple[int, int]:
        """
        Parses test pass/fail counts from pytest output.
        Returns (passed, total).
        """
        combined = f"{stdout}\n{stderr}"
        passed = 0
        failed = 0

        # Pattern 1: e.g. "5 passed, 1 failed" or "4 passed in 0.05s"
        pass_match = re.search(r"(\d+)\s+passed", combined)
        if pass_match:
            passed = int(pass_match.group(1))

        fail_match = re.search(r"(\d+)\s+failed", combined)
        if fail_match:
            failed = int(fail_match.group(1))

        error_match = re.search(r"(\d+)\s+error", combined)
        if error_match:
            failed += int(error_match.group(1))

        total = passed + failed
        if total == 0:
            # Check for binary search / custom runner pattern: "[TEST_RESULT] PASSED: 5/5"
            custom_match = re.search(r"PASSED:\s*(\d+)/(\d+)", combined)
            if custom_match:
                passed = int(custom_match.group(1))
                total = int(custom_match.group(2))

        return passed, total

    def evaluate_task_result(
        self,
        task: BenchmarkTask,
        generated_files: Dict[str, str],
        exit_code: int,
        stdout: str,
        stderr: str,
        duration_seconds: float,
        model_time_seconds: float = 0.0,
        test_time_seconds: float = 0.0,
        model_calls: int = 1,
        repair_attempts: int = 0,
        token_count: Optional[int] = None,
        regressions: int = 0
    ) -> TaskMetricScores:
        """
        Evaluates task execution against requirements, tests, and code quality.
        """
        scores = TaskMetricScores()
        scores.duration_seconds = round(duration_seconds, 2)
        scores.model_time_seconds = round(model_time_seconds, 2)
        scores.test_time_seconds = round(test_time_seconds, 2)
        scores.model_calls = model_calls
        scores.repair_attempts = repair_attempts
        scores.token_count = token_count
        scores.regressions = regressions

        # 1. Functional Correctness
        passed_tests, total_tests = self.parse_pytest_counts(stdout, stderr)
        scores.tests_passed = passed_tests
        scores.tests_total = total_tests
        scores.build_success = (exit_code == 0)

        if total_tests > 0:
            scores.functional_correctness = round((passed_tests / total_tests) * 100.0, 1)
        elif scores.build_success:
            # it compiles, but no test ran: correctness is not demonstrated, so it is not credited
            scores.functional_correctness = 0.0
        else:
            scores.functional_correctness = 0.0

        # 2. Requirement Adherence
        criteria_met = 0
        total_criteria = max(1, len(task.acceptance_criteria))

        # Check required artifacts exist and are not empty
        artifacts_present = all(
            art in generated_files and len(generated_files[art].strip()) > 0
            for art in task.required_artifacts
        )
        if artifacts_present:
            criteria_met += 1

        # Check specific acceptance criteria heuristics
        for criterion in task.acceptance_criteria:
            crit_lower = criterion.lower()
            met = False
            for fname, content in generated_files.items():
                content_lower = content.lower()
                # Check function/class names mentioned in criteria
                if "parse_query_string" in crit_lower and "def parse_query_string" in content:
                    met = True
                elif "build_query_string" in crit_lower and "def build_query_string" in content:
                    met = True
                elif "itemcreate" in crit_lower and "itemcreate" in content_lower:
                    met = True
                elif "app" in crit_lower and "fastapi()" in content_lower:
                    met = True
                elif "lrucache" in crit_lower and "class lrucache" in content_lower:
                    met = True
                elif "filter_by_price_range" in crit_lower and "def filter_by_price_range" in content:
                    met = True
                elif "validate_registration_payload" in crit_lower and "def validate_registration_payload" in content:
                    met = True
                elif "api_reference" in crit_lower and fname.lower() == "api_reference.md" and len(content) > 300:
                    met = True
                elif "all test cases pass" in crit_lower or "hidden validation tests" in crit_lower:
                    met = (scores.functional_correctness >= 99.0)

            if met:
                criteria_met += 1

        criteria_met = min(criteria_met, total_criteria)
        scores.criteria_met = criteria_met
        scores.criteria_total = total_criteria
        scores.requirement_adherence = round((criteria_met / total_criteria) * 100.0, 1)

        # 3. Code Quality (AST Syntax & Structure)
        syntax_valid = True
        has_type_hints = False
        clean_ast = True

        for fname, content in generated_files.items():
            if fname.endswith(".py"):
                try:
                    tree = ast.parse(content)
                    # Check for type annotations in AST
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if node.returns is not None or any(arg.annotation for arg in node.args.args):
                                has_type_hints = True
                except SyntaxError:
                    syntax_valid = False
                    clean_ast = False

        scores.syntax_valid = syntax_valid
        scores.lint_clean = clean_ast and syntax_valid
        scores.type_check_passed = has_type_hints

        quality_score = 0.0
        if syntax_valid:
            quality_score += 50.0
        if clean_ast:
            quality_score += 25.0
        if has_type_hints:
            quality_score += 25.0
        scores.code_quality = quality_score

        # 4. Reliability
        if not scores.build_success and scores.functional_correctness == 0:
            scores.reliability = 0.0
        else:
            base_rel = 100.0
            # Deduct for repair attempts (cost of unreliability)
            base_rel -= min(30.0, repair_attempts * 10.0)
            # Deduct for regressions
            base_rel -= min(40.0, regressions * 20.0)
            scores.reliability = max(0.0, round(base_rel, 1))

        # 5. Composite Overall Score
        # Weights: Correctness 40%, Adherence 20%, Quality 15%, Reliability 15%, Speed 10%
        speed_score = max(0.0, 100.0 - (duration_seconds / max(1.0, task.timeout_seconds)) * 100.0)

        composite = (
            0.40 * scores.functional_correctness +
            0.20 * scores.requirement_adherence +
            0.15 * scores.code_quality +
            0.15 * scores.reliability +
            0.10 * speed_score
        )
        scores.overall_score = round(composite, 1)

        return scores


global_objective_evaluator = ObjectiveEvaluator()
