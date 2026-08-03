"""
AIForge Day 8 Complexity & Strategy Benchmark Verification Script
==================================================================
Runs ComplexityEvaluator against all 130 golden test cases and measures accuracy,
overuse/underuse rates, and latency.
"""

import sys
import json
import time
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.evaluation.evaluators.complexity_evaluator import global_complexity_evaluator
from backend.reasoning.complexity_analyzer import global_complexity_analyzer
from backend.reasoning.strategy_selector import global_strategy_selector


def run_benchmark():
    dataset_path = project_root / "backend" / "evaluation" / "datasets" / "golden_dataset.json"
    with open(dataset_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    print(f"Loaded {len(test_cases)} Golden Test Cases from dataset.")

    start_time = time.perf_counter()
    metrics = global_complexity_evaluator.evaluate(test_cases)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    print("\n================================================================================")
    print(" [DAY 8 COMPLEXITY & ADAPTIVE REASONING BENCHMARK REPORT]")
    print("================================================================================")
    print(f" Total Golden Test Cases Evaluated   : {len(test_cases)}")
    print(f" Complexity Classification Accuracy  : {metrics['complexity_accuracy']:.1f}%  (Target >= 90.0%)")
    print(f" Strategy Selection Accuracy        : {metrics['strategy_accuracy']:.1f}%  (Target >= 95.0%)")
    print(f" Workflow Activation Accuracy       : {metrics['workflow_activation_accuracy']:.1f}% (Target 100.0%)")
    print(f" Planning Overuse Rate (Simple)     : {metrics['planning_overuse_rate']:.1f}%   (Target < 5.0%)")
    print(f" Planning Underuse Rate (Complex)   : {metrics['planning_underuse_rate']:.1f}%  (Target < 5.0%)")
    print(f" Benchmark Processing Latency        : {elapsed_ms:.2f} ms ({elapsed_ms/len(test_cases):.3f} ms / item)")
    print("================================================================================\n")


if __name__ == "__main__":
    run_benchmark()
