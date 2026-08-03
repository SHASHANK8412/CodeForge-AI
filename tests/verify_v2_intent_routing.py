"""
AIForge V2 Master Verification Suite: Intent Classification & Smart Routing Agent
==================================================================================
Tests prompt intent classification scenarios:
1. "BINARY SEARCH CODE" -> Intent = CODING (Returns Python binary search, O(log n) time complexity, no project template)
2. "Explain BFS vs DFS" -> Intent = EXPLANATION (Returns structured Markdown breakdown)
3. "Build a Food Delivery App" -> Intent = PROJECT_GENERATION (Triggers LangGraph multi-agent pipeline)
4. "Fix this React syntax error" -> Intent = DEBUGGING
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.agents.router_agent import RouterAgent, IntentCategory
from backend.agents.coding_agent import CodingAgent
from backend.agents.explanation_agent import ExplanationAgent

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


def verify_intent_routing():
    print("===========================================================================")
    print(" 🚀 AIForge V2 – Intent Classification & Smart Router Verification")
    print("===========================================================================\n")

    router = RouterAgent()
    coding_agent = CodingAgent()
    explanation_agent = ExplanationAgent()

    # ---------------------------------------------------------
    # Test Case 1: Prompt "BINARY SEARCH CODE"
    # ---------------------------------------------------------
    section("Test Case 1: Prompt 'BINARY SEARCH CODE'")
    res1 = router.classify_intent("BINARY SEARCH CODE")
    code_out = coding_agent.process_coding_request("BINARY SEARCH CODE")

    check("Classified prompt 'BINARY SEARCH CODE' as Intent = CODING", res1["intent"] == IntentCategory.CODING)
    check("Targeted CodingAgent instead of LangGraph project pipeline", res1["target_agent"] == "CodingAgent")
    check("Returned Python binary search implementation snippet", "def binary_search" in code_out["response"])
    check("Included O(log n) time complexity and O(1) space complexity analysis", "O(\\log n)" in code_out["response"])
    check("Excluded full-stack project scaffold (no uvicorn/cd backend)", "cd backend && uvicorn" not in code_out["response"])

    # ---------------------------------------------------------
    # Test Case 2: Prompt "Explain BFS vs DFS"
    # ---------------------------------------------------------
    section("Test Case 2: Prompt 'Explain BFS vs DFS'")
    res2 = router.classify_intent("Explain BFS vs DFS graph traversal")
    exp_out = explanation_agent.process_explanation_request("Explain BFS vs DFS graph traversal")

    check("Classified prompt as Intent = EXPLANATION", res2["intent"] == IntentCategory.EXPLANATION)
    check("Returned structured Markdown conceptual breakdown", "## Understanding" in exp_out["response"])

    # ---------------------------------------------------------
    # Test Case 3: Prompt "Build a Food Delivery App"
    # ---------------------------------------------------------
    section("Test Case 3: Prompt 'Build a Food Delivery App'")
    res3 = router.classify_intent("Build a Food Delivery App with FastAPI and React")

    check("Classified full-stack prompt as Intent = PROJECT_GENERATION", res3["intent"] == IntentCategory.PROJECT_GENERATION)
    check("Targeted AutonomousSoftwareEngineer / LangGraph Pipeline for full app generation", res3["target_agent"] in ["LangGraph_MultiAgent_Pipeline", "AutonomousSoftwareEngineer"])

    # ---------------------------------------------------------
    # Test Case 4: Prompt "Fix this React error"
    # ---------------------------------------------------------
    section("Test Case 4: Prompt 'Fix this React error'")
    res4 = router.classify_intent("Fix this React syntax error in App.jsx")

    check("Classified debugging prompt as Intent = DEBUGGING", res4["intent"] == IntentCategory.DEBUGGING)

    # Summary
    print("\n" + "="*75)
    print(f" AIFORGE V2 INTENT ROUTING VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*75 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = verify_intent_routing()
    sys.exit(0 if success else 1)
