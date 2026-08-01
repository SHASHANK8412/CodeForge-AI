"""
AIForge Intent Classification & Precision Routing Test Suite
============================================================
Verifies:
1. "Develop a Formula 1 website" -> PROJECT_GENERATION
2. "Build a cricket website" -> PROJECT_GENERATION
3. "Create food delivery application" -> PROJECT_GENERATION
4. "Solve Two Sum" -> DSA_PROBLEM
5. "Binary search implementation in Python" -> CODE_GENERATION
6. "Why is my React component crashing?" -> DEBUGGING
7. "Explain quicksort" -> EXPLANATION
8. "Formula 1" -> AMBIGUOUS
9. "Cricket" -> AMBIGUOUS

Eliminates universal CodingAgent fallback.
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.agents.router_agent import global_router_agent, IntentCategory

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


def run_routing_test():
    print("===========================================================================")
    print(" 🚀 AIForge Precision Intent Router Verification Suite")
    print("===========================================================================\n")

    test_cases = [
        ("Develop a Formula 1 website", IntentCategory.PROJECT_GENERATION),
        ("Build a cricket website", IntentCategory.PROJECT_GENERATION),
        ("Create food delivery application", IntentCategory.PROJECT_GENERATION),
        ("Solve Two Sum", IntentCategory.DSA_PROBLEM),
        ("Binary search implementation in Python", IntentCategory.CODE_GENERATION),
        ("Why is my React component crashing?", IntentCategory.DEBUGGING),
        ("Explain quicksort", IntentCategory.EXPLANATION),
        ("Formula 1", IntentCategory.AMBIGUOUS),
        ("Cricket", IntentCategory.AMBIGUOUS),
    ]

    for prompt, expected_intent in test_cases:
        info = global_router_agent.classify_intent(prompt)
        intent = info["intent"]
        
        is_ok = check(
            f"'{prompt}' -> Expected: {expected_intent} | Got: {intent}",
            intent == expected_intent,
            f"Selected Agent: {info['target_agent']} | Reason: {info['reason']}"
        )

    print("\n" + "="*75)
    print(f" ROUTING VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: { _results['passed'] } | Failed: { _results['failed'] }")
    print("="*75 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = run_routing_test()
    sys.exit(0 if success else 1)
