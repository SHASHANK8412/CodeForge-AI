"""
AIForge V2 Day 9 Verification Suite
====================================
End-to-end verification script for AIForge V2 Day 9 deliverables:
1. Testing Agent (Autonomous Test Generation, Execution & Quality Validation Engine)
2. Unit, Integration, API, and Database Test Generators
3. Playwright E2E Browser Automation Test Generator
4. Locust Performance Load Benchmark Generator
5. OWASP Security & Vulnerability Test Generator
6. Coverage.py Analysis Engine (Overall Coverage >= 80%)
7. Test Execution Engine (Pass/Fail Tracking)
8. LangGraph Autonomous Workflow (CEO -> Manager -> Planner -> Architect -> Frontend -> Backend -> Database -> Reviewer -> Testing -> END)
9. FastAPI Endpoint (POST /api/v2/testing/generate)
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from v2.agents.testing.agent import global_testing_agent_v2
from v2.agents.testing.validator import global_testing_validator
from v2.orchestrator.workflow_v2 import workflow_v2_graph

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


async def run_v2_day9_verification():
    print("======================================================================")
    print(" 🧪 AIForge V2 – Day 9 Autonomous Test Generation & Quality Validation Verification")
    print("======================================================================\n")

    # 1. Test Generation & Execution Test: AI Resume Analyzer
    prompt = "Generate test suite for an AI Resume Analyzer project."
    section("1. Full-Stack Test Cases Generation & Execution")
    report = global_testing_agent_v2.generate_tests(prompt, project_id="v2_day9_verify")

    check("Generated Pytest & Vitest Unit test cases", len(report.unit_tests) >= 2)
    check("Generated Integration & HTTPX API test cases", len(report.integration_tests) >= 1 and len(report.api_tests) >= 2)
    check("Generated PostgreSQL Database CRUD test cases", len(report.database_tests) >= 1)
    check("Generated Playwright E2E browser automation test specs", len(report.e2e_tests) >= 1)

    section("2. Performance, Security & Coverage Analysis")
    check("Generated Locust performance load benchmark tests", len(report.performance_tests) >= 1)
    check("Generated OWASP security & SQLi vulnerability tests", len(report.security_tests) >= 1)
    check("Calculated overall code coverage percentage (>= 80.0%)", report.coverage.overall_coverage_pct >= 80.0)

    section("3. Test Execution Engine & Overall Status")
    check("Executed test suites with 0 failing tests", report.failed_count == 0)
    check("Overall test suite status PASSED", report.overall_status == "PASSED")

    section("4. LangGraph Autonomous Workflow (CEO -> Manager -> Planner -> Architect -> Frontend -> Backend -> Database -> Reviewer -> Testing)")
    initial_state = {
        "user_prompt": prompt,
        "ceo_evaluation": None,
        "tasks": None,
        "planner_output": None,
        "architect_output": None,
        "frontend_output": None,
        "backend_output": None,
        "database_output": None,
        "reviewer_output": None,
        "testing_output": None,
        "messages": []
    }
    final_state = await workflow_v2_graph.ainvoke(initial_state)

    check("LangGraph graph executed CEO -> Manager -> Planner -> Architect -> Frontend -> Backend -> Database -> Reviewer -> Testing seamlessly", final_state.get("testing_output") is not None)
    check("Inter-Agent event stream logged FULLSTACK_TESTING_COMPLETED event", any(m.get("event") == "FULLSTACK_TESTING_COMPLETED" for m in final_state.get("messages", [])))

    # Summary
    print("\n" + "="*70)
    print(f" AIFORGE V2 DAY 9 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


def main():
    return asyncio.run(run_v2_day9_verification())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
