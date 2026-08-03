"""
AIForge Day 11 Repository Intelligence Benchmark Verification Script
=====================================================================
Evaluates Relevant File Precision & Recall, Context Reduction Ratio (> 95%),
Repository Task Success Rate (>= 90%), Secret Redaction Pass Rate (100%),
and Path Security Pass Rate (100%) across the Golden Dataset.
"""

import json
import time
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.evaluation.evaluators.repository_evaluator import global_repository_evaluator


def run_benchmark():
    dataset_path = Path("backend/evaluation/datasets/golden_dataset.json")
    if not dataset_path.exists():
        print(f"Error: Golden dataset not found at {dataset_path}")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    print(f"Loaded {len(test_cases)} Golden Test Cases from dataset.")

    t0 = time.time()
    metrics = global_repository_evaluator.evaluate(test_cases)
    elapsed = (time.time() - t0) * 1000.0

    print("\n" + "=" * 80)
    print(" [DAY 11 REPOSITORY INTELLIGENCE BENCHMARK REPORT]")
    print("=" * 80)
    print(f" Total Golden Test Cases Evaluated   : {len(test_cases)}")
    print(f" Relevant File Precision            : {metrics['relevant_file_precision']}%")
    print(f" Relevant File Recall               : {metrics['relevant_file_recall']}%")
    print(f" Context Reduction Ratio            : {metrics['context_reduction_ratio']}% (Target >= 95.0%)")
    print(f" Repository Task Success Rate       : {metrics['repository_task_success_rate']}% (Target >= 90.0%)")
    print(f" Secret Redaction Pass Rate         : {metrics['secret_redaction_pass_rate']}% (Target 100.0%)")
    print(f" Path Security Pass Rate            : {metrics['path_security_pass_rate']}% (Target 100.0%)")
    print(f" Evaluation Processing Latency      : {elapsed:.2f} ms ({elapsed / len(test_cases):.3f} ms / item)")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_benchmark()
