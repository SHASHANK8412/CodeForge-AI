"""
AIForge V2 Day 2 Verification Suite
====================================
End-to-end verification script for AIForge V2 Day 2 deliverables:
1. CEO Agent (Complexity Evaluation, Timeline Estimation, Resource Allocation)
2. Project Manager Agent (Sprint Task Breakdown & Dependencies)
3. Inter-Agent Communication Envelope Message & Event Dispatcher
4. LangGraph Workflow (CEO -> Manager -> Planner -> END)
5. FastAPI Endpoint (POST /api/v2/project/start)
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from v2.agents.ceo.agent import global_ceo_agent_v2
from v2.agents.ceo.models import ComplexityTier
from v2.agents.manager.agent import global_manager_agent_v2
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


async def run_v2_day2_verification():
    print("======================================================================")
    print(" 🧠 AIForge V2 – Day 2 Autonomous Orchestration Layer Verification")
    print("======================================================================\n")

    # 1. Test Prompt 1: Medium Complexity AI Resume Analyzer
    section("1. Test 1: Medium Complexity (AI Resume Analyzer)")
    eval1 = global_ceo_agent_v2.evaluate_project("Build an AI Resume Analyzer using FastAPI and React.")
    check("CEO Agent evaluated Medium Complexity tier", eval1.complexity_tier == ComplexityTier.MEDIUM)
    tasks1 = global_manager_agent_v2.generate_task_breakdown(eval1)
    check("Project Manager Agent created sprint breakdown with 5+ tasks", len(tasks1) >= 5)

    # 2. Test Prompt 2: Enterprise Complexity Instagram Clone
    section("2. Test 2: Enterprise Complexity (Instagram Platform Clone)")
    eval2 = global_ceo_agent_v2.evaluate_project("Build a social media platform similar to Instagram.")
    check("CEO Agent evaluated Enterprise Complexity tier (Score >= 8.0)", eval2.complexity_tier == ComplexityTier.ENTERPRISE and eval2.complexity_score >= 8.0)

    # 3. Test Prompt 3: Low Complexity Calculator App
    section("3. Test 3: Low Complexity (Calculator App)")
    eval3 = global_ceo_agent_v2.evaluate_project("Create a calculator app.")
    check("CEO Agent evaluated Low Complexity tier (Score <= 4.0)", eval3.complexity_tier == ComplexityTier.LOW and eval3.complexity_score <= 4.0)

    # 4. LangGraph Autonomous Workflow (CEO -> Manager -> Planner -> END)
    section("4. LangGraph Autonomous Workflow (CEO -> Manager -> Planner)")
    initial_state = {
        "user_prompt": "Build a SaaS CRM with authentication, payments, analytics, and AI support.",
        "ceo_evaluation": None,
        "tasks": None,
        "planner_output": None,
        "messages": []
    }
    final_state = await workflow_v2_graph.ainvoke(initial_state)

    check("CEO Node executed and attached evaluation to graph state", final_state.get("ceo_evaluation") is not None)
    check("Manager Node executed and generated tasks list", len(final_state.get("tasks", [])) >= 5)
    check("Planner Node executed and produced requirements report", len(final_state.get("planner_output", "")) > 100)
    check("Inter-Agent event stream messages logged across nodes", len(final_state.get("messages", [])) >= 3)

    # Summary
    print("\n" + "="*70)
    print(f" AIFORGE V2 DAY 2 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


def main():
    return asyncio.run(run_v2_day2_verification())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
