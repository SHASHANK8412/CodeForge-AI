"""
AIForge V2 Day 32 Verification Suite
=====================================
End-to-end verification script for AIForge V2 Day 32 deliverables:
1. Error Monitor Failure Captures Across 10 System Sources (API, Test, Build, Runtime, DB, Docker, CI/CD, etc.)
2. Root Cause Analysis (RCA) Engine (Distinguishing Symptoms from Underlying Root Causes)
3. Self-Healing Code Patch Generation & Test Validation
4. Configurable Retry Strategy & Human Escalation Policy (Attempts 1-3 -> Escalate)
5. Learning Store Knowledge Persistence (Recurring Failures & Proven Solutions)
6. Self-Healing Dashboard Metrics & REST APIs
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.self_healing.error_monitor import global_error_monitor, FailureSource
from backend.self_healing.root_cause import global_root_cause_analyzer
from backend.self_healing.fix_generator import global_fix_generator
from backend.self_healing.learning_store import global_learning_store
from backend.self_healing.retry_manager import global_retry_manager

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


def run_v2_day32_verification():
    print("======================================================================")
    print(" 🛠️ AIForge V2 – Day 32 Autonomous Debugging & Self-Healing Verification")
    print("======================================================================\n")

    section("1. Error Monitor & Failure Capture")
    err_report = global_error_monitor.record_error(
        error_type=FailureSource.DATABASE_ERROR,
        message="Database connection pool exhausted timeout",
        file="backend/database.py",
        line=84,
        severity="High"
    )
    check("Recorded Database connection failure report", err_report["error_type"] == FailureSource.DATABASE_ERROR)

    errors = global_error_monitor.get_errors()
    check("Retrieved monitored error reports", len(errors) >= 2)

    section("2. Root Cause Analysis (RCA) Engine")
    rca = global_root_cause_analyzer.analyze(err_report)
    check("Identified root cause from error symptoms", "DB Pool Size" in rca["root_cause"] and len(rca["symptoms"]) >= 2)

    section("3. Automated Fix Generator & Validation")
    fix = global_fix_generator.generate_and_apply_fix(rca)
    check("Generated self-healing patch & validated tests", fix["validation_status"] == "SUCCESS")

    section("4. Learning Store Knowledge Persistence")
    lesson = global_learning_store.record_lesson(
        problem="Database Connection Timeout",
        root_cause=rca["root_cause"],
        solution=rca["recommended_fix"],
        was_successful=True
    )
    check("Persisted failure lesson to Learning Store", lesson["occurrences"] >= 1 and "pool_size" in lesson["solution"])

    all_lessons = global_learning_store.get_all_lessons()
    check("Retrieved recurring failure lessons", len(all_lessons) >= 2)

    section("5. Retry Manager & Escalation Loop")
    # Execute successful retry attempt
    retry_res1 = global_retry_manager.execute_self_healing_attempt(err_report)
    check("Executed self-healing attempt 1 (Resolved)", retry_res1["status"] == "RESOLVED" and not retry_res1["escalated"])

    # Simulate exhausting retries for persistent failure
    stub_error = {"error_id": "err_escalate_test", "error_type": "Docker", "message": "Container panic", "file": "Dockerfile"}
    for _ in range(3):
        global_retry_manager.execute_self_healing_attempt(stub_error)

    retry_res_escalated = global_retry_manager.execute_self_healing_attempt(stub_error)
    check("Escalated to human review after max retry limit reached", retry_res_escalated["escalated"] and retry_res_escalated["status"] == "ESCALATED")

    section("6. Self-Healing Dashboard Metrics")
    dashboard = global_retry_manager.get_self_healing_dashboard()
    check("Compiled Self-Healing Dashboard data", "success_rate_percentage" in dashboard["metrics"] and len(dashboard["reusable_lessons"]) >= 2)

    # Summary
    print("\n" + "="*70)
    print(f" AIFORGE V2 DAY 32 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = run_v2_day32_verification()
    sys.exit(0 if success else 1)
