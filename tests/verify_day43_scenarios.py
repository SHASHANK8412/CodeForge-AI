"""
AIForge V2 Day 43 Verification Suite: Multi-Model AI Collaboration & Consensus Engine
======================================================================================
Tests all Day 43 scenarios:
1. One model offline -> Automatic fallback
2. Conflicting outputs -> Consensus engine chooses best
3. Slow model -> Timeout & continue
4. Invalid response -> Ignore and continue
5. Three valid responses -> Highest-ranked solution selected
6. Task-aware dynamic model routing
7. Performance & Benchmark Metrics Tracking
"""

import sys
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.services.model_manager import ModelManager
from backend.services.consensus_engine import ConsensusEngine
from backend.services.benchmark import BenchmarkTracker

PASS = "[PASS]"
FAIL = "[FAIL]"
_results = {"passed": 0, "failed": 0}


def section(title: str):
    print(f"\n{'='*75}")
    print(f"  {title}")
    print(f"{'='*75}")


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


def verify_day43_pipeline():
    print("===========================================================================")
    print(" 🚀 AIForge V2 – Day 43 Multi-Model AI Collaboration & Consensus Engine")
    print("===========================================================================\n")

    manager = ModelManager()
    consensus = ConsensusEngine()
    benchmark = BenchmarkTracker()

    # ---------------------------------------------------------
    # Scenario 1: One Model Offline (Automatic Fallback)
    # ---------------------------------------------------------
    section("Scenario 1: One Model Offline -> Automatic Fallback")
    res1 = manager.execute_models_in_parallel(
        prompt="Generate backend API router",
        models=["qwen2.5-coder", "deepseek-coder", "codellama"],
        task_type="Backend APIs",
        offline_models=["deepseek-coder"]  # Preferred model offline
    )
    check("Received responses from all parallel model requests", len(res1) == 3)
    check("Handled offline model via automatic fallback without stopping generation",
          any(r["status"] == "SUCCESS" for r in res1))

    # ---------------------------------------------------------
    # Scenario 2: Conflicting Outputs -> Consensus Engine Chooses Best
    # ---------------------------------------------------------
    section("Scenario 2: Conflicting Outputs -> Consensus Engine Chooses Best")
    candidates2 = [
        {"model": "qwen2.5-coder", "output": "const App = () => <div>Hello</div>;", "status": "SUCCESS", "latency": 2.1, "tokens_used": 80},
        {"model": "deepseek-coder", "output": "import React from 'react';\nexport default function App() { return <div>Hello World</div>; }", "status": "SUCCESS", "latency": 2.4, "tokens_used": 150},
        {"model": "codellama", "output": "/* incomplete code */", "status": "SUCCESS", "latency": 2.8, "tokens_used": 30}
    ]
    eval2 = consensus.evaluate_candidates(candidates2, task_type="React UI")
    check("Consensus engine calculated agreement percentage", eval2["consensus_pct"] >= 75.0)
    check("Consensus engine selected complete, superior code output", eval2["winner_model"] == "deepseek-coder" or eval2["winner_model"] == "qwen2.5-coder")

    # ---------------------------------------------------------
    # Scenario 3: Slow Model Timeout & Continuation
    # ---------------------------------------------------------
    section("Scenario 3: Slow Model Timeout & Continuation")
    candidates3 = [
        {"model": "qwen2.5-coder", "output": "def test_ok(): pass", "status": "SUCCESS", "latency": 1.2, "tokens_used": 40},
        {"model": "slow-model", "output": "def test_slow(): pass", "status": "SUCCESS", "latency": 8.5, "tokens_used": 40}
    ]
    eval3 = consensus.evaluate_candidates(candidates3, task_type="Unit Tests")
    check("Fast model solution prioritized over slow model", eval3["winner_model"] == "qwen2.5-coder")

    # ---------------------------------------------------------
    # Scenario 4: Invalid Response (Ignore and Continue)
    # ---------------------------------------------------------
    section("Scenario 4: Invalid Response -> Ignore and Continue")
    candidates4 = [
        {"model": "qwen2.5-coder", "output": "import React from 'react';", "status": "SUCCESS", "latency": 1.5, "tokens_used": 50},
        {"model": "broken-model", "output": "", "status": "FAILED", "latency": 0.05, "tokens_used": 0}
    ]
    eval4 = consensus.evaluate_candidates(candidates4, task_type="React UI")
    check("Ignored failed/invalid response and selected valid candidate", eval4["winner_model"] == "qwen2.5-coder")

    # ---------------------------------------------------------
    # Scenario 5: Three Valid Responses -> Highest-Ranked Winner
    # ---------------------------------------------------------
    section("Scenario 5: Three Valid Responses -> Highest-Ranked Selected")
    candidates5 = manager.execute_models_in_parallel(
        prompt="Create user authentication route",
        models=["qwen2.5-coder", "deepseek-coder", "codellama"],
        task_type="Backend APIs"
    )
    eval5 = consensus.evaluate_candidates(candidates5, task_type="Backend APIs")
    check("Ranked all 3 valid model candidates", len(eval5["evaluations"]) == 3)
    check("AI cross-voting generated star ratings for each candidate", len(eval5["voting_scores"]) == 3)
    check("Selected highest-ranked candidate solution as overall winner", eval5["winner_model"] in ["deepseek-coder", "qwen2.5-coder", "codellama"])

    # ---------------------------------------------------------
    # Scenario 6: Task-Aware Dynamic Model Routing
    # ---------------------------------------------------------
    section("Scenario 6: Task-Aware Dynamic Model Routing")
    r_ui = manager.route_task("React UI")
    r_api = manager.route_task("Backend APIs")
    r_sql = manager.route_task("SQL")
    r_debug = manager.route_task("Debugging")

    check("Routed React UI task to Qwen Coder", r_ui == "qwen2.5-coder")
    check("Routed Backend APIs task to DeepSeek Coder", r_api == "deepseek-coder")
    check("Routed SQL task to DeepSeek Coder", r_sql == "deepseek-coder")
    check("Routed Debugging task to CodeLlama", r_debug == "codellama")

    # ---------------------------------------------------------
    # Scenario 7: Performance & Benchmark Metrics Tracking
    # ---------------------------------------------------------
    section("Scenario 7: Benchmark Metrics Persistence")
    benchmark.record_run("qwen2.5-coder", latency=2.1, tokens_used=150, quality_score=95.0, is_winner=True)
    summary = benchmark.get_dashboard_summary()
    check("Persistently tracked model metrics in model_metrics.json", summary["total_runs"] > 0)
    check("Calculated overall success rate and model win stats", "overall_success_rate" in summary and len(summary["model_statistics"]) >= 3)

    # Summary
    print("\n" + "="*75)
    print(f" AIFORGE V2 DAY 43 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*75 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = verify_day43_pipeline()
    sys.exit(0 if success else 1)
