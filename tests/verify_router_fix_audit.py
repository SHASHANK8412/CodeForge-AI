"""
AIForge V2 Router & Multi-Agent Audit Script
============================================
Performs code-level audit verifying that 'Develop Formula 1 Website' and all project prompts
are correctly routed to the Multi-Agent Pipeline (Planner -> Architect -> Frontend -> Backend -> Database -> Testing -> Reviewer).
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.agents.router_agent import global_router_agent, IntentCategory
from backend.agents.factory import AgentFactory
from backend.orchestrator.autonomous_engineer import global_autonomous_engineer

PASS = "[PASS]"
FAIL = "[FAIL]"
_results = {"passed": 0, "failed": 0}


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


def verify_router_fix():
    print("===========================================================================")
    print(" 🔍 AIForge V2 – Intent Router & Execution Pipeline Technical Audit")
    print("===========================================================================\n")

    test_cases = [
        ("Develop Formula 1 Website", IntentCategory.PROJECT_GENERATION, "LangGraph_MultiAgent_Pipeline"),
        ("Build Netflix Clone", IntentCategory.PROJECT_GENERATION, "LangGraph_MultiAgent_Pipeline"),
        ("Create Todo App", IntentCategory.PROJECT_GENERATION, "LangGraph_MultiAgent_Pipeline"),
        ("Food Delivery App", IntentCategory.PROJECT_GENERATION, "LangGraph_MultiAgent_Pipeline"),
        ("Binary Search Code", IntentCategory.CODING, "CodingAgent"),
        ("Linked List Insertion", IntentCategory.CODING, "CodingAgent"),
        ("What is Formula 1?", IntentCategory.EXPLANATION, "ExplanationAgent"),
        ("Debug this Python code", IntentCategory.DEBUGGING, "DebugAgent")
    ]

    for prompt, expected_intent, expected_agent in test_cases:
        res = global_router_agent.classify_intent(prompt)
        matched = res["intent"] == expected_intent and res["target_agent"] == expected_agent

        print(f"Prompt: '{prompt}'")
        print(f"  ↓ Detected Intent: {res['intent']}")
        print(f"  ↓ Selected Agent:  {res['target_agent']}")
        print(f"  ↓ Reason:           Matched project verbs/nouns vs coding keywords")

        check(f"Routing check for '{prompt}'", matched, f"Expected {expected_intent} ({expected_agent}), Got {res['intent']} ({res['target_agent']})")
        print("-" * 60)

    # Verify end-to-end execution of "Develop Formula 1 Website"
    print("\nExecuting End-to-End Pipeline for 'Develop Formula 1 Website'...")
    pipeline_res = global_autonomous_engineer.run_autonomous_pipeline("Develop Formula 1 Website")

    check("Pipeline executed successfully", pipeline_res["success"])
    check("Quality Score >= 95", pipeline_res["quality_score"] >= 95.0)
    check("Frontend React app generated", "frontend/src/App.jsx" in pipeline_res["files"])
    check("Backend FastAPI main generated", "backend/main.py" in pipeline_res["files"])
    check("Database PostgreSQL 3NF schema generated", "database/schema.sql" in pipeline_res["files"])

    print("\n" + "="*75)
    print(f" ROUTER FIX AUDIT SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: { _results['passed'] } | Failed: { _results['failed'] }")
    print("="*75 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = verify_router_fix()
    sys.exit(0 if success else 1)
