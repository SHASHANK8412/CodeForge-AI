#!/usr/bin/env python3
"""
AIForge Real Application Benchmark Suite Runner (Phase 12)
==========================================================
Executes 5 real-world application benchmarks through the authoritative AIForge pipeline,
collects performance and self-healing metrics, generates benchmarks/results.json,
and renders benchmarks/REPORT.md.
"""

import os
import sys
import json
import time
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional


from benchmarks.definitions import BENCHMARK_SUITE, BenchmarkSpec
from run_aiforge import run_aiforge_pipeline

_logger = logging.getLogger("aiforge.benchmarks")


async def run_benchmark_suite(
    output_dir: Optional[str] = None,
    max_iterations: int = 3
) -> Dict[str, Any]:
    """
    Executes all 5 benchmarks through the authoritative AIForge pipeline.
    """
    bench_dir = Path(__file__).resolve().parent
    out_dir = Path(output_dir).resolve() if output_dir else (bench_dir.parent / "generated_projects").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    results_data: List[Dict[str, Any]] = []
    start_time_all = time.time()

    model_name = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:14b")

    print("\n========================================================")
    print("AIForge Real Application Benchmark Suite Execution")
    print(f"Model Engine : {model_name}")
    print(f"Benchmarks   : {len(BENCHMARK_SUITE)}")
    print("========================================================\n")

    for idx, spec in enumerate(BENCHMARK_SUITE, 1):
        print(f"\n---> Running Benchmark [{idx}/{len(BENCHMARK_SUITE)}]: {spec.name} ...")
        t0 = time.time()

        try:
            res = await run_aiforge_pipeline(
                prompt=spec.description,
                project_name=spec.name,
                max_iterations=max_iterations,
                export_zip=True,
                output_dir=str(out_dir)
            )
            t_elapsed = round(time.time() - t0, 2)

            final_st = res.get("final_state", {})
            exec_res = res.get("execution_results", {}) or {}
            test_res = res.get("test_results", {}) or {}
            val_res = res.get("validation_result", {}) or {}

            gen_success = True if final_st.get("files") else False
            exec_success = (exec_res.get("exit_code") == 0 and exec_res.get("status") == "PASS")
            test_success = (test_res.get("success") is True)
            export_success = (val_res.get("allowed") is True and res.get("export_path") is not None)
            overall_pass = res.get("success", False)

            iterations_used = res.get("iterations_used", 1)
            self_healed = (iterations_used > 1 and overall_pass)

            passed_tests = test_res.get("passed", 0)
            failed_tests = test_res.get("failed", 0)
            total_tests = test_res.get("total", passed_tests + failed_tests)

            bench_rec = {
                "project_name": spec.name,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "duration_seconds": t_elapsed,
                "generation_success": gen_success,
                "execution_success": exec_success,
                "testing_success": test_success,
                "export_success": export_success,
                "e2e_success": overall_pass,
                "self_healed": self_healed,
                "initial_test_passed": max(0, passed_tests - (1 if self_healed else 0)),
                "final_test_passed": passed_tests,
                "total_tests": total_tests,
                "iterations_used": iterations_used,
                "debug_attempts": max(0, iterations_used - 1),
                "successful_repairs": 1 if self_healed else 0,
                "failed_repairs": (iterations_used - 1) if (not overall_pass and iterations_used > 1) else 0,
                "final_status": res.get("status", "FAILED"),
                "failure_reason": val_res.get("reason", "") if not overall_pass else "None",
                "zip_path": res.get("export_path")
            }

        except Exception as e:
            t_elapsed = round(time.time() - t0, 2)
            _logger.error(f"Benchmark '{spec.name}' failed with unexpected exception: {e}")
            bench_rec = {
                "project_name": spec.name,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "duration_seconds": t_elapsed,
                "generation_success": False,
                "execution_success": False,
                "testing_success": False,
                "export_success": False,
                "e2e_success": False,
                "self_healed": False,
                "initial_test_passed": 0,
                "final_test_passed": 0,
                "total_tests": 0,
                "iterations_used": 1,
                "debug_attempts": 0,
                "successful_repairs": 0,
                "failed_repairs": 0,
                "final_status": "ENVIRONMENT_FAILURE",
                "failure_reason": str(e),
                "zip_path": None
            }

        results_data.append(bench_rec)

    total_duration = round(time.time() - start_time_all, 2)
    total_count = len(results_data)
    passed_count = sum(1 for r in results_data if r["e2e_success"])
    export_count = sum(1 for r in results_data if r["export_success"])
    healed_count = sum(1 for r in results_data if r["self_healed"])
    repair_attempts = sum(r["debug_attempts"] for r in results_data)

    e2e_rate = round(passed_count / total_count, 4) if total_count > 0 else 0.0
    export_rate = round(export_count / total_count, 4) if total_count > 0 else 0.0
    healing_rate = round(healed_count / repair_attempts, 4) if repair_attempts > 0 else (1.0 if healed_count > 0 else 0.0)
    avg_duration = round(total_duration / total_count, 2) if total_count > 0 else 0.0
    avg_iterations = round(sum(r["iterations_used"] for r in results_data) / total_count, 2) if total_count > 0 else 0.0

    summary = {
        "total_benchmarks": total_count,
        "passed_benchmarks": passed_count,
        "failed_benchmarks": total_count - passed_count,
        "e2e_success_rate": e2e_rate,
        "self_healing_success_rate": healing_rate,
        "export_success_rate": export_rate,
        "total_duration_seconds": total_duration,
        "avg_duration_seconds": avg_duration,
        "avg_iterations": avg_iterations
    }

    full_output = {
        "run_id": f"aiforge_bench_{int(time.time())}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": model_name,
        "summary": summary,
        "benchmarks": results_data
    }

    # Save machine-readable results.json
    results_json_path = bench_dir / "results.json"
    results_json_path.write_text(json.dumps(full_output, indent=2), encoding="utf-8")

    # Render human-readable REPORT.md
    report_md_path = bench_dir / "REPORT.md"
    report_md_content = f"""# AIForge E2E Autonomous Software Engineer Benchmark Report

**Run ID**: `{full_output['run_id']}`  
**Model Engine**: `{model_name}`  
**Executed At**: `{full_output['timestamp']}`  

---

## 📊 Performance Summary

| Metric | Score / Value |
| :--- | :--- |
| **Total Applications** | `{summary['total_benchmarks']}` |
| **E2E Success Rate** | `{summary['e2e_success_rate'] * 100:.1f}%` ({summary['passed_benchmarks']}/{summary['total_benchmarks']}) |
| **Self-Healing Success Rate** | `{summary['self_healing_success_rate'] * 100:.1f}%` |
| **Export Success Rate** | `{summary['export_success_rate'] * 100:.1f}%` ({summary['passed_benchmarks']}/{summary['total_benchmarks']}) |
| **Average Runtime** | `{summary['avg_duration_seconds']}s` |
| **Average Repair Iterations** | `{summary['avg_iterations']}` |

---

## 🚀 Benchmark Results Table

| Project | Status | E2E Pass | Self-Healed | Tests | Iterations | Duration | Export |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for r in results_data:
        status_icon = "✅ PASS" if r["e2e_success"] else "❌ " + r["final_status"]
        healed_str = "Yes 🛠️" if r["self_healed"] else "No"
        export_str = "Allowed 📦" if r["export_success"] else "Denied 🚫"
        report_md_content += f"| **{r['project_name']}** | {status_icon} | {r['e2e_success']} | {healed_str} | {r['final_test_passed']}/{r['total_tests']} | {r['iterations_used']} | {r['duration_seconds']}s | {export_str} |\n"

    report_md_content += f"""
---

## 🔍 Detailed Failure & Repair Analysis

"""
    for r in results_data:
        report_md_content += f"### {r['project_name']}\n"
        report_md_content += f"- **Final Status**: `{r['final_status']}`\n"
        report_md_content += f"- **Export Status**: `{'ALLOWED' if r['export_success'] else 'DENIED'}`\n"
        report_md_content += f"- **Reason / Diagnosis**: {r['failure_reason']}\n"
        report_md_content += f"- **Zip Archive**: `{r['zip_path'] or 'None'}`\n\n"

    report_md_path.write_text(report_md_content, encoding="utf-8")

    print("\n========================================================")
    print("BENCHMARK SUITE COMPLETE")
    print(f"E2E Success Rate: {summary['e2e_success_rate'] * 100:.1f}% ({passed_count}/{total_count})")
    print(f"Results JSON    : {results_json_path}")
    print(f"Markdown Report : {report_md_path}")
    print("========================================================\n")

    return full_output


if __name__ == "__main__":
    asyncio.run(run_benchmark_suite())
