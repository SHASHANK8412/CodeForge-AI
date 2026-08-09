"""
AIForge V2 Day 34 Verification Suite
=====================================
End-to-end verification script for AIForge V2 Day 34 deliverables:
1. Multi-LLM Model Registry Metadata across 8 Models (Qwen, DeepSeek, Llama, Mistral, Gemma, GPT-4o, Claude)
2. Task-Based Intelligent Model Selector (Coding, Architecture, Documentation, Reasoning)
3. Multi-Model Retry & Fallback Strategy Execution Chain
4. 7-Dimension Response Evaluator & Ensemble Mode Multi-Model Output Comparison
5. Benchmark Engine Metrics (Latency, Token Throughput, Memory, Cost, Success Rate)
6. Multi-LLM Dashboard Metrics & REST APIs
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.llm.model_registry import global_model_registry
from backend.llm.model_selector import global_model_selector
from backend.llm.fallback import global_fallback_manager
from backend.llm.evaluator import global_response_evaluator
from backend.llm.benchmark import global_benchmark_engine
from backend.llm.router import global_dynamic_model_router

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


def run_v2_day34_verification():
    print("======================================================================")
    print(" 🤖 AIForge V2 – Day 34 Multi-LLM Intelligence & Routing Verification")
    print("======================================================================\n")

    section("1. Multi-LLM Model Registry Metadata")
    all_models = global_model_registry.get_all_models()
    check("Registered metadata for 8 supported LLM models", len(all_models) == 8)

    qwen_meta = global_model_registry.get_model_metadata("QwenCoder")
    check("Retrieved metadata for Qwen Coder", qwen_meta["supports_code"] and qwen_meta["provider"] == "Ollama")

    section("2. Task-Based Intelligent Model Selector")
    coding_sel = global_model_selector.select_best_model(task_type="coding", prompt="Write python REST endpoint")
    check("Routed coding task to Qwen Coder", coding_sel["selected_model"] == "Qwen Coder")

    arch_sel = global_model_selector.select_best_model(task_type="architecture", prompt="Design microservices blueprint")
    check("Routed architecture task to DeepSeek Coder", arch_sel["selected_model"] == "DeepSeek Coder")

    doc_sel = global_model_selector.select_best_model(task_type="documentation", prompt="Write README markdown docs")
    check("Routed documentation task to Llama 3.x", doc_sel["selected_model"] == "Llama 3.x")

    section("3. Model Fallback Chain Execution")
    fallback_res = global_fallback_manager.execute_with_fallback(primary_model="FailingModel", prompt="Generate module")
    check("Fallback chain executed successfully when primary model failed", fallback_res["was_fallback_used"] and fallback_res["successful_model"] != "FailingModel")

    section("4. 7-Dimension Response Evaluator & Ensemble Mode")
    eval_score = global_response_evaluator.evaluate_response("Qwen Coder", "def get_users(): return []", "Get users")
    check("Scored response across 7 quality dimensions", eval_score["overall_score"] > 80.0 and "accuracy" in eval_score["dimension_scores"])

    ensemble_res = global_dynamic_model_router.route_and_generate(prompt="Build auth system", ensemble_mode=True)
    check("Executed Ensemble mode & selected highest scoring model", ensemble_res["mode"] == "Ensemble" and "best_model" in ensemble_res)

    section("5. Benchmark Engine Metrics")
    bench = global_benchmark_engine.run_benchmark(model_names=["Qwen Coder", "DeepSeek Coder", "GPT-4o"])
    check("Generated LLM benchmark metrics report", len(bench["results"]) == 3 and bench["results"][0]["latency_ms"] > 0)

    section("6. Multi-LLM Dashboard Metrics")
    dashboard = global_dynamic_model_router.get_router_dashboard()
    check("Compiled Multi-LLM Dashboard metrics", dashboard["supported_models_count"] == 8 and dashboard["success_rate_percentage"] > 90.0)

    # Summary
    print("\n" + "="*70)
    print(f" AIFORGE V2 DAY 34 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = run_v2_day34_verification()
    sys.exit(0 if success else 1)
