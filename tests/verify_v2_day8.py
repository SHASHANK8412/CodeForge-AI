"""
AIForge V2 Day 8 Verification Suite
====================================
End-to-end verification script for AIForge V2 Day 8 deliverables:
1. Reviewer Agent (Autonomous Code Review, Quality Assurance & Refactoring Generator)
2. Architecture, Frontend, Backend, and Database Review Engines
3. Security Vulnerability Analysis Engine (SQLi, XSS, CSRF, JWT, RBAC)
4. Performance Analysis Engine (N+1 queries, unindexed FKs, Redis caching)
5. Code Quality Metrics Engine (Maintainability index, Cyclomatic complexity, overall quality score)
6. Autonomous Refactoring Engine
7. LangGraph Autonomous Workflow (CEO -> Manager -> Planner -> Architect -> Frontend -> Backend -> Database -> Reviewer -> END)
8. FastAPI Endpoint (POST /api/v2/review/generate)
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from v2.agents.reviewer.agent import global_reviewer_agent_v2
from v2.agents.reviewer.validator import global_reviewer_validator
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


async def run_v2_day8_verification():
    print("======================================================================")
    print(" 🔍 AIForge V2 – Day 8 Autonomous Code Review & Quality Audit Verification")
    print("======================================================================\n")

    # 1. Code Review Generation Test: AI Resume Analyzer
    prompt = "Review an AI Resume Analyzer project."
    section("1. Multi-Dimensional Code Review & Quality Category Scores")
    report = global_reviewer_agent_v2.review_project(prompt, project_id="v2_day8_verify")

    check("Scored all 7 quality dimensions (Architecture, Frontend, Backend, DB, Security, Performance, Quality)", len(report.category_scores) >= 7)
    check("Generated overall quality score (>= 80%)", report.overall_score >= 80.0)

    section("2. Security, Performance & Refactoring Engines")
    check("Security vulnerability audit identified & logged security issues", len(report.issues) >= 1)
    check("Performance checker evaluated N+1 queries & Redis caching", any(cs.category_name == "Performance" for cs in report.category_scores))
    check("Refactoring engine generated priority code improvement suggestions", len(report.refactorings) >= 1)

    section("3. Code Quality Metrics & Approval Status")
    check("Calculated Maintainability Index (> 80.0)", report.metrics.maintainability_index > 80.0)
    check("Calculated Cyclomatic Complexity (< 5.0)", report.metrics.cyclomatic_complexity < 5.0)
    check("Review report status approved", report.build_status == "approved")

    section("4. LangGraph Autonomous Workflow (CEO -> Manager -> Planner -> Architect -> Frontend -> Backend -> Database -> Reviewer)")
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
        "messages": []
    }
    final_state = await workflow_v2_graph.ainvoke(initial_state)

    check("LangGraph graph executed CEO -> Manager -> Planner -> Architect -> Frontend -> Backend -> Database -> Reviewer seamlessly", final_state.get("reviewer_output") is not None)
    check("Inter-Agent event stream logged PROJECT_CODE_REVIEW_COMPLETED event", any(m.get("event") == "PROJECT_CODE_REVIEW_COMPLETED" for m in final_state.get("messages", [])))

    # Summary
    print("\n" + "="*70)
    print(f" AIFORGE V2 DAY 8 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


def main():
    return asyncio.run(run_v2_day8_verification())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
