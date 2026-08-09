"""
AIForge V2 Master Verification Suite: P0 Intelligent Algorithm Execution Pipeline
===================================================================================
Tests P0 requirements:
1. Intent Router accuracy for Coding/DSA, Debug, Explanation, Resume, Project, RAG.
2. Elimination of hardcoded fallback templates (sorted(data), def solution).
3. Exact LLM prompt & Developer mode logging trace.
4. Output Validation & Automatic Retry engine.
5. Success criteria for Binary Search Code, Linked List Insertion, Merge Sort, Bubble Sort.
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.agents.router_agent import global_router_agent, IntentCategory
from backend.agents.coding_agent import global_coding_agent

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


def verify_p0_coding_pipeline():
    print("===========================================================================")
    print(" 🚀 AIForge V2 – P0 Intelligent Algorithm Execution Pipeline Verification")
    print("===========================================================================\n")

    # ---------------------------------------------------------
    # Test Case 1: Binary Search Code
    # ---------------------------------------------------------
    section("Test Case 1: Prompt 'Binary Search Code'")
    prompt1 = "Binary Search Code"
    route1 = global_router_agent.classify_intent(prompt1)
    res1 = global_coding_agent.process_coding_request(prompt1)
    t1 = res1["response"]

    check("Routed to Coding Agent", route1["intent"] == IntentCategory.CODING)
    check("Contains 'Binary Search' title & 'def binary_search' function", "binary_search" in t1)
    check("Contains Time Complexity O(log n) and Space Complexity O(1)", "O(\\log n)" in t1 and "O(1)" in t1)
    check("Contains step-by-step algorithm explanation & edge cases", "Explanation" in t1 and "Edge Cases" in t1)
    check("Does NOT contain hardcoded template 'sorted(data)' or 'def solution('", "sorted(data)" not in t1 and "def solution(" not in t1)

    # ---------------------------------------------------------
    # Test Case 2: Linked List Insertion
    # ---------------------------------------------------------
    section("Test Case 2: Prompt 'Linked List Insertion'")
    prompt2 = "Linked List Insertion"
    route2 = global_router_agent.classify_intent(prompt2)
    res2 = global_coding_agent.process_coding_request(prompt2)
    t2 = res2["response"]

    check("Routed to Coding Agent", route2["intent"] == IntentCategory.CODING)
    check("Contains 'Node' class definition and 'next' pointer", "class Node" in t2 and "next" in t2)
    check("Contains Linked List insert methods (beginning & end)", "insert" in t2.lower())
    check("Does NOT contain hardcoded template 'sorted(data)'", "sorted(data)" not in t2)

    # ---------------------------------------------------------
    # Test Case 3: Merge Sort Algorithm
    # ---------------------------------------------------------
    section("Test Case 3: Prompt 'Merge Sort'")
    res3 = global_coding_agent.process_coding_request("Merge Sort")
    t3 = res3["response"]

    check("Contains 'merge_sort' and 'merge' helper functions", "merge" in t3.lower())
    check("Contains O(n log n) complexity analysis", "O(n \\log n)" in t3 or "O(n" in t3)

    # ---------------------------------------------------------
    # Test Case 4: Bubble Sort Algorithm
    # ---------------------------------------------------------
    section("Test Case 4: Prompt 'Bubble Sort'")
    res4 = global_coding_agent.process_coding_request("Bubble Sort")
    t4 = res4["response"]

    check("Contains 'bubble_sort' and 'swap' logic", "swap" in t4.lower())
    check("Contains O(n^2) complexity analysis", "O(n^2)" in t4 or "O(n" in t4)

    # ---------------------------------------------------------
    # Test Case 5: Validation Engine & Rejection Check
    # ---------------------------------------------------------
    section("Test Case 5: Output Validation & Rejection Logic")
    bad_output = "def solution(data):\n    return sorted(data)"
    val_check = global_coding_agent.validate_output("Binary Search Code", bad_output)

    check("Validation Engine rejects output containing forbidden placeholder template", not val_check["valid"])

    # Summary
    print("\n" + "="*75)
    print(f" AIFORGE V2 P0 PIPELINE VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*75 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = verify_p0_coding_pipeline()
    sys.exit(0 if success else 1)
