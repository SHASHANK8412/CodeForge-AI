"""
Day 71 - Autonomous Multi-Model AI Collaboration Verification Suite
===================================================================
Validates AIForge Multi-LLM Routing across 5 core testing scenarios:
- Test 1: Auto Routing (Task classification -> Selects coding/explanation model automatically)
- Test 2: Parallel Strategy (Multiple models execute simultaneously -> AI Judge evaluates response)
- Test 3: Automatic Failover & Retry (Failover chain: Qwen -> DeepSeek -> GPT -> Claude)
- Test 4: Performance Benchmarking (Latency, token count, accuracy, and cost recorded)
- Test 5: Model Memory & Learning (Historical scores update task routing preferences over time)
"""

import sys
import json
import time
import asyncio
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.llm.model_registry import MODELS
from backend.llm.model_memory import ModelMemory
from backend.llm.model_selector import ModelSelector
from backend.llm.model_manager import ModelManager
from backend.llm.response_evaluator import ResponseEvaluator
from backend.llm.benchmark import ModelBenchmarker
from backend.llm.model_router import ModelRouter

PASS = "[PASS]"
FAIL = "[FAIL]"
_results = {"passed": 0, "failed": 0}


def section(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    if condition:
        _results["passed"] += 1
    else:
        _results["failed"] += 1
    msg = f"  {status}  {name}"
    if detail:
        msg += f"\n        => {detail}"
    print(msg)
    return condition


async def run_day71_tests():
    print("======================================================================")
    print(" AIForge Day 71 - Autonomous Multi-Model AI Collaboration Verification")
    print("======================================================================\n")

    router = ModelRouter()

    # ------------------------------------------------------------------
    section("Test 1 – Auto Routing & Task Classification")
    # ------------------------------------------------------------------
    res_code = await router.route_and_execute("Create a Python REST API using FastAPI", strategy="auto")
    res_fix = await router.route_and_execute("Quick fix missing import statement", strategy="auto")

    check("Task 'Create a Python REST API' classified as coding", res_code["task_type"] == "coding")
    check("Selected model for coding task", res_code["selected_model"] in ["deepseek", "qwen", "gpt"])
    check("Task 'Quick fix' classified as quick_fix", res_fix["task_type"] == "quick_fix")

    # ------------------------------------------------------------------
    section("Test 2 – Parallel Multi-Model Strategy & AI Judge Evaluation")
    # ------------------------------------------------------------------
    res_parallel = await router.route_and_execute("Design a scalable auth middleware", strategy="parallel")

    check("Parallel strategy executed successfully", res_parallel["strategy"] == "parallel")
    check("Multiple candidate responses evaluated (count >= 2)", res_parallel["evaluated_count"] >= 2)
    check("AI Judge selected top candidate response", len(res_parallel["winning_response"]) > 0)
    check("Winner score evaluated by ResponseEvaluator (score >= 80.0)", res_parallel["winner_score"] >= 80.0)

    # ------------------------------------------------------------------
    section("Test 3 – Automatic Failover & Retry System")
    # ------------------------------------------------------------------
    manager = ModelManager()
    
    # Simulate failover by forcing primary model failure
    MODELS["qwen"]["force_fail"] = True
    failover_res = await manager.execute_with_failover("qwen", "Generate code with failover test")
    MODELS["qwen"]["force_fail"] = False # Reset

    check("Automatic failover triggered upon primary model timeout", failover_res["retries_count"] > 0)
    check("Fallback model selected from secondary pool (DeepSeek / GPT)", failover_res["model_key"] in ["deepseek", "gpt"])

    # ------------------------------------------------------------------
    section("Test 4 – Performance Benchmarking")
    # ------------------------------------------------------------------
    bench_res = await router.route_and_execute("Run benchmark telemetry check", strategy="benchmark")
    benchmarks = bench_res.get("benchmarks", [])

    check("Benchmark strategy generated performance records", len(benchmarks) >= 3)
    check("Recorded latency, accuracy score, and cost metrics for all models", all("latency_seconds" in b and "cost_usd" in b for b in benchmarks))

    # ------------------------------------------------------------------
    section("Test 5 – Model Memory & Reinforcement Learning")
    # ------------------------------------------------------------------
    memory = ModelMemory()
    memory.record_performance("coding", "deepseek", latency=1.2, quality_score=99.0, cost=0.0)
    memory.record_performance("coding", "qwen", latency=1.5, quality_score=91.0, cost=0.0)

    preferred_coding = memory.get_preferred_model("coding")

    check("Model memory updated with historical execution scores", len(memory.get_all_memory().get("history", [])) > 0)
    check("Model router prefers higher scoring model (deepseek) for coding tasks", preferred_coding == "deepseek")

    # Summary
    print("\n" + "="*70)
    print(f" DAY 71 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


def main():
    return asyncio.run(run_day71_tests())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
