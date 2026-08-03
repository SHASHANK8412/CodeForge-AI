"""
AIForge Day 10 Execution Sandbox Benchmark Verification Script
===============================================================
Runs ExecutionEvaluator against all 185 golden test cases and measures eligibility accuracy,
sandbox security pass rate, self-debug success rate, and latency.
"""

import sys
import json
import time
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.evaluation.evaluators.execution_evaluator import global_execution_evaluator


def run_benchmark():
    dataset_path = project_root / "backend" / "evaluation" / "datasets" / "golden_dataset.json"
    with open(dataset_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    print(f"Loaded {len(test_cases)} Golden Test Cases from dataset.")

    start_time = time.perf_counter()
    metrics = global_execution_evaluator.evaluate(test_cases)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    print("\n================================================================================")
    print(" [DAY 10 SECURE CODE EXECUTION SANDBOX BENCHMARK REPORT]")
    print("================================================================================")
    print(f" Total Golden Test Cases Evaluated   : {len(test_cases)}")
    print(f" Execution Eligibility Accuracy     : {metrics['eligibility_accuracy']:.1f}%  (Target >= 95.0%)")
    print(f" Sandbox Security Pass Rate         : {metrics['sandbox_security_pass_rate']:.1f}% (Target 100.0%)")
    print(f" Self-Debug Success Rate            : {metrics['self_debug_success_rate']:.1f}% (Target >= 80.0%)")
    print(f" Functional Correctness Gain        : +{metrics['functional_correctness_gain']:.1f}%")
    print(f" Evaluation Processing Latency      : {elapsed_ms:.2f} ms ({elapsed_ms/len(test_cases):.3f} ms / item)")
    print("================================================================================\n")


if __name__ == "__main__":
    run_benchmark()
