"""
AIForge Autonomous SDE Evaluation & Benchmark Suite
===================================================
Executes unseen full-stack application generation benchmarks and evaluates:
- Generation success rate (%)
- Build success rate (%)
- Test pass rate (%)
- Average execution duration (sec)
- Average self-healing repair attempts
"""

import sys
import asyncio
import time
import json
from pathlib import Path

# Ensure repo root in sys.path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.graph.execution_healing_loop import global_execution_healing_loop

BENCHMARK_PROMPTS = [
    "Build a React + FastAPI todo application with PostgreSQL and authentication",
    "Build a SaaS expense tracker app with REST API and JWT auth",
    "Build a markdown blog engine with SQLite database",
    "Build a real-time team chat system with websockets",
    "Build an AI prompt manager app with FastAPI and React"
]

async def run_benchmarks():
    print("=" * 70)
    print("🚀 STARTING AIFORGE AUTONOMOUS SOFTWARE ENGINEER BENCHMARK SUITE")
    print("=" * 70)

    total_prompts = len(BENCHMARK_PROMPTS)
    passed_generations = 0
    passed_builds = 0
    total_time = 0.0
    total_repair_attempts = 0

    results = []

    for i, prompt in enumerate(BENCHMARK_PROMPTS, 1):
        print(f"\n[Benchmark {i}/{total_prompts}] Prompt: '{prompt}'")
        start_time = time.perf_counter()

        try:
            res = await global_execution_healing_loop.run_autonomous_workflow(prompt, session_id=f"bench_{i}")
            duration = round(time.perf_counter() - start_time, 2)
            total_time += duration

            status = res.get("status", "FAILED")
            exec_rep = res.get("execution_report", {})
            repair_attempts = exec_rep.get("attempt", 1)
            total_repair_attempts += repair_attempts

            is_gen_success = status in ["SUCCESS", "COMPLETED_WITH_WARNINGS"]
            is_build_success = exec_rep.get("status") == "PASS"

            if is_gen_success:
                passed_generations += 1
            if is_build_success:
                passed_builds += 1

            results.append({
                "prompt": prompt,
                "status": status,
                "duration_sec": duration,
                "repair_attempts": repair_attempts,
                "build_passed": is_build_success,
                "deliverable_valid": res.get("execution_report", {}).get("deliverable_validation", {}).get("is_valid", False)
            })

            print(f"  Result: {status} | Build: {'PASS' if is_build_success else 'FAIL'} | Time: {duration}s | Repair Attempts: {repair_attempts}")

        except Exception as err:
            duration = round(time.perf_counter() - start_time, 2)
            print(f"  ❌ Benchmark execution error: {err}")
            results.append({
                "prompt": prompt,
                "status": "ERROR",
                "duration_sec": duration,
                "error": str(err)
            })

    gen_pass_rate = round((passed_generations / total_prompts) * 100, 1)
    build_pass_rate = round((passed_builds / total_prompts) * 100, 1)
    avg_duration = round(total_time / total_prompts, 2)
    avg_repairs = round(total_repair_attempts / total_prompts, 2)

    print("\n" + "=" * 70)
    print("📊 BENCHMARK SUMMARY RESULTS")
    print("=" * 70)
    print(f"Total Benchmark Applications Evaluated: {total_prompts}")
    print(f"Generation Success Rate:               {gen_pass_rate}% ({passed_generations}/{total_prompts})")
    print(f"Build & Sandbox Pass Rate:             {build_pass_rate}% ({passed_builds}/{total_prompts})")
    print(f"Average Generation Duration:           {avg_duration} sec")
    print(f"Average Self-Healing Repair Attempts:   {avg_repairs}")
    print("=" * 70)

    summary_file = repo_root / "evaluation" / "benchmark_latest.json"
    summary_file.write_text(json.dumps({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "generation_success_rate": gen_pass_rate,
        "build_pass_rate": build_pass_rate,
        "avg_duration_sec": avg_duration,
        "avg_repair_attempts": avg_repairs,
        "results": results
    }, indent=2), encoding="utf-8")
    print(f"Saved benchmark report to: {summary_file.name}")

if __name__ == "__main__":
    asyncio.run(run_benchmarks())
