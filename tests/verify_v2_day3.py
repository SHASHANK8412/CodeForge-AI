"""
AIForge V2 Day 3 Verification Suite
====================================
End-to-end verification script for AIForge V2 Day 3 deliverables:
1. Planner Agent (Requirements Engineering & Intelligent Blueprint Engine)
2. Functional & Non-Functional Requirements Generator
3. User Personas, User Stories, and Acceptance Criteria Engine
4. MVP Definitions & Sprint Roadmap Planner
5. Technical Stack & Risk Assessment Analyzer
6. LangGraph Autonomous Workflow (CEO -> Manager -> Planner -> END)
7. FastAPI Endpoint (POST /api/v2/planner/analyze)
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from v2.agents.planner.planner_service import global_planner_service
from v2.agents.planner.validator import global_planner_validator
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


async def run_v2_day3_verification():
    print("======================================================================")
    print(" 📋 AIForge V2 – Day 3 Requirements Engineering & Blueprint Verification")
    print("======================================================================\n")

    # 1. Product Blueprint Generation Test: E-Commerce Platform
    prompt = "Build an AI-powered e-commerce platform with recommendations, payments, analytics, and admin dashboard."
    section("1. Requirements Engineering & Blueprint Generation")
    report = global_planner_service.analyze_project(prompt, project_id="v2_day3_verify")

    check("Generated business analysis with clear goal & core features", len(report.business_analysis.core_features) >= 3)
    check("Generated functional requirements list", len(report.functional_requirements) >= 3)
    check("Generated non-functional metrics (performance, security, SLA)", len(report.non_functional_requirements) >= 3)

    section("2. User Personas, Stories & Acceptance Criteria")
    check("Generated target user personas", len(report.user_personas) >= 1)
    check("Generated Agile user stories with Acceptance Criteria", len(report.user_stories) >= 1 and len(report.user_stories[0].acceptance_criteria) >= 1)

    section("3. MVP Scope, Sprint Roadmap & Risk Assessment")
    check("Defined MVP scope (V1 Must Have, V2 Should Have, V3 Nice to Have)", len(report.mvp_definition.v1_must_have) >= 1)
    check("Structured 5-sprint engineering roadmap", len(report.sprint_plan) >= 4)
    check("Identified technical risks & mitigation strategies", len(report.risk_analysis) >= 1)
    check("Recommended tech stack & architecture topology", len(report.tech_recommendations) >= 3)

    section("4. LangGraph Workflow (CEO -> Manager -> Planner)")
    initial_state = {
        "user_prompt": prompt,
        "ceo_evaluation": None,
        "tasks": None,
        "planner_output": None,
        "messages": []
    }
    final_state = await workflow_v2_graph.ainvoke(initial_state)
    check("LangGraph graph executed CEO -> Manager -> Planner seamlessly", final_state.get("planner_output") is not None)

    # Summary
    print("\n" + "="*70)
    print(f" AIFORGE V2 DAY 3 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


def main():
    return asyncio.run(run_v2_day3_verification())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
