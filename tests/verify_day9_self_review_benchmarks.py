"""
AIForge Day 9 Self-Review Benchmark Verification Script
========================================================
Runs SelfReviewEvaluator against all 155 golden test cases and measures accuracy,
review rates, and latency.
"""

import sys
import json
import time
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.evaluation.evaluators.self_review_evaluator import global_self_review_evaluator


def run_benchmark():
    dataset_path = project_root / "backend" / "evaluation" / "datasets" / "golden_dataset.json"
    with open(dataset_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    print(f"Loaded {len(test_cases)} Golden Test Cases from dataset.")

    start_time = time.perf_counter()
    metrics = global_self_review_evaluator.evaluate(test_cases)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    print("\n================================================================================")
    print(" [DAY 9 INTELLIGENT SELF-REVIEW & REFLECTION BENCHMARK REPORT]")
    print("================================================================================")
    print(f" Total Golden Test Cases Evaluated   : {len(test_cases)}")
    print(f" Review Policy Accuracy             : {metrics['policy_accuracy']:.1f}%  (Target >= 85.0%)")
    print(f" Simple Prompt Review Rate          : {metrics['simple_prompt_review_rate']:.1f}%   (Target < 5.0%)")
    print(f" Complex Prompt Review Rate         : {metrics['complex_prompt_review_rate']:.1f}%  (Target >= 80.0%)")
    print(f" Successful Refinement Rate         : {metrics['successful_refinement_rate']:.1f}% (Target >= 80.0%)")
    print(f" Negative Refinement Rate           : {metrics['negative_refinement_rate']:.1f}%   (Target < 5.0%)")
    print(f" Evaluation Processing Latency      : {elapsed_ms:.2f} ms ({elapsed_ms/len(test_cases):.3f} ms / item)")
    print("================================================================================\n")


if __name__ == "__main__":
    run_benchmark()
