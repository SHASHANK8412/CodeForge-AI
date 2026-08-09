"""
AIForge V2 Day 42 Verification Suite: Intelligent Error Detection & Self-Healing Pipeline
===========================================================================================
Tests all 8 Day 42 error detection & self-healing scenarios:
1. Missing Python package
2. Syntax error in generated code
3. Missing React import
4. PostgreSQL connection failure
5. Docker build failure
6. FastAPI router missing
7. Runtime exception
8. Unknown error handling (confidence < 60% stops retries and outputs diagnostic report)
"""

import sys
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.agents.error_analyzer import ErrorAnalyzerAgent
from backend.agents.root_cause import RootCauseFinder
from backend.agents.self_healing import SelfHealingAgent
from backend.services.retry_manager import RetryManagerService
from backend.utils.log_parser import LogParser

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


def verify_day42_pipeline():
    print("===========================================================================")
    print(" 🚀 AIForge V2 – Day 42 Intelligent Error Detection & Self-Healing Pipeline")
    print("===========================================================================\n")

    analyzer = ErrorAnalyzerAgent()
    rca_finder = RootCauseFinder()
    healer = SelfHealingAgent(project_root=project_root)
    retry_svc = RetryManagerService(max_retries=3)

    # ---------------------------------------------------------
    # Scenario 1: Missing Python Package
    # ---------------------------------------------------------
    section("Scenario 1: Missing Python Package")
    log_pkg = """
Traceback (most recent call last):
  File "backend/main.py", line 21, in <module>
ModuleNotFoundError: No module named 'fastapi'
    """
    analysis1 = analyzer.analyze_log(log_pkg)
    rca1 = rca_finder.analyze(analysis1)
    res1 = healer.attempt_fix(analysis1)
    check("Categorized ModuleNotFoundError", analysis1["error_type"] == "ModuleNotFoundError")
    check("Identified Root Cause & Suggested Fix", "fastapi" in rca1["suggested_fix"].lower())
    check("Applied package install suggestion and fix", res1["success"] and res1["confidence"] >= 60)

    # ---------------------------------------------------------
    # Scenario 2: Syntax Error in Generated Code
    # ---------------------------------------------------------
    section("Scenario 2: Syntax Error in Generated Code")
    log_syntax = """
  File "backend/services/calculator.py", line 42
    def compute(x, y)
                    ^
SyntaxError: expected ':'
    """
    analysis2 = analyzer.analyze_log(log_syntax)
    rca2 = rca_finder.analyze(analysis2)
    res2 = healer.attempt_fix(analysis2)
    check("Identified SyntaxError in file & line", analysis2["error_type"] == "SyntaxError" and analysis2["line"] == 42)
    check("Root cause indicates syntax repair required", "syntax" in rca2["root_cause"].lower())
    check("Applied targeted patch code fix", res2["success"])

    # ---------------------------------------------------------
    # Scenario 3: Missing React Import
    # ---------------------------------------------------------
    section("Scenario 3: Missing React Import")
    log_react = "Failed to resolve import \"react\" or Module not found: Can't resolve 'react' in src/App.jsx:1"
    analysis3 = analyzer.analyze_log(log_react)
    rca3 = rca_finder.analyze(analysis3)
    res3 = healer.attempt_fix(analysis3)
    check("Categorized React MissingImport", analysis3["category"] == "React" and analysis3["error_type"] == "MissingImport")
    check("Suggested adding React import statement", "import" in rca3["suggested_fix"].lower())
    check("Successfully patched missing import", res3["success"])

    # ---------------------------------------------------------
    # Scenario 4: PostgreSQL Connection Failure
    # ---------------------------------------------------------
    section("Scenario 4: PostgreSQL Connection Failure")
    log_db = "psycopg2.OperationalError: connection to server at '127.0.0.1', port 5432 failed: Connection refused"
    analysis4 = analyzer.analyze_log(log_db)
    rca4 = rca_finder.analyze(analysis4)
    res4 = healer.attempt_fix(analysis4)
    check("Categorized PostgreSQL connection failure", analysis4["error_type"] == "PostgreSQLConnectionRefused")
    check("Detected DB_HOST / DB_PORT configuration cause", "backend/.env" in rca4["suggested_fix"])
    check("Updated database configuration file", res4["success"])

    # ---------------------------------------------------------
    # Scenario 5: Docker Build Failure
    # ---------------------------------------------------------
    section("Scenario 5: Docker Build Failure")
    log_docker = "ERROR: failed to solve: process '/bin/sh -c pip install' exited with code: 1 in Dockerfile"
    analysis5 = analyzer.analyze_log(log_docker)
    rca5 = rca_finder.analyze(analysis5)
    res5 = healer.attempt_fix(analysis5)
    check("Categorized Docker build failure", analysis5["error_type"] == "DockerBuildFailed")
    check("Identified Dockerfile instruction issue", "dockerfile" in rca5["suggested_fix"].lower())
    check("Applied Dockerfile fix patch", res5["success"])

    # ---------------------------------------------------------
    # Scenario 6: FastAPI Router Missing
    # ---------------------------------------------------------
    section("Scenario 6: FastAPI Router Missing")
    log_router = "AttributeError: 'FastAPI' object has no attribute 'include_router' or router missing in backend/main.py:25"
    analysis6 = analyzer.analyze_log(log_router)
    rca6 = rca_finder.analyze(analysis6)
    res6 = healer.attempt_fix(analysis6)
    check("Categorized FastAPI MissingRouter", analysis6["error_type"] == "MissingRouter")
    check("Suggested include_router registration", "include_router" in rca6["suggested_fix"])
    check("Applied router registration fix", res6["success"])

    # ---------------------------------------------------------
    # Scenario 7: Runtime Exception (Stack Trace Capture)
    # ---------------------------------------------------------
    section("Scenario 7: Runtime Exception (Stack Trace Capture)")
    log_runtime = """
Traceback (most recent call last):
  File "backend/services/user_service.py", line 88, in get_user
    return user_dict["email"]
KeyError: 'email'
    """
    analysis7 = analyzer.analyze_log(log_runtime)
    rca7 = rca_finder.analyze(analysis7)
    res7 = healer.attempt_fix(analysis7)
    check("Captured KeyError exception and line number", analysis7["error_type"] == "KeyError" and analysis7["line"] == 88)
    check("Targeted fix suggests adding null / key guard", "guard" in rca7["suggested_fix"].lower() or "check" in rca7["suggested_fix"].lower())
    check("Applied targeted code repair", res7["success"])

    # ---------------------------------------------------------
    # Scenario 8: Unknown Error (Confidence < 60% Halt)
    # ---------------------------------------------------------
    section("Scenario 8: Unknown Error (Confidence < 60% Abort)")
    log_unknown = "Unclassified totally obscure hardware failure 0x88127391823"
    analysis8 = analyzer.analyze_log(log_unknown)
    rca8 = rca_finder.analyze(analysis8)
    res8 = healer.attempt_fix(analysis8)
    pipeline_res8 = retry_svc.run_self_healing_pipeline(log_unknown, project_id="proj_scenario_8")

    check("Low confidence score for unknown error (< 60%)", rca8["confidence_score"] < 60)
    check("Self-healing halted without infinite retries", not res8["success"] and res8["status"] == "ABORTED_LOW_CONFIDENCE")
    check("Generated human-readable diagnostic report", "human_readable_report" in pipeline_res8 and "AIForge Diagnostic Report" in pipeline_res8["human_readable_report"])

    # ---------------------------------------------------------
    # Scenario 9: Error History & Dashboard Metrics
    # ---------------------------------------------------------
    section("Scenario 9: Persistence & Dashboard Metrics")
    metrics = retry_svc.get_dashboard_metrics()
    history = retry_svc.load_history()
    check("Persisted error history entries to error_history.json", len(history) >= 1)
    check("Calculated Dashboard Metrics (Errors Found, Fixed, Retries, Confidence, Build Success %)",
          "errors_found" in metrics and "errors_fixed" in metrics and "build_success_pct" in metrics)

    # Summary
    print("\n" + "="*75)
    print(f" AIFORGE V2 DAY 42 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*75 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = verify_day42_pipeline()
    sys.exit(0 if success else 1)
