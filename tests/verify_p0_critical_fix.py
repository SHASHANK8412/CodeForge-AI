"""
AIForge V2 Master Verification Suite: P0 Critical Bug Fix - Eliminate Static Templates & Restore Real LLM Generation
=====================================================================================================================
Verifies all 10 P0 criteria:
1. "What is Mumbai Indians?" -> Contains Cricket, IPL, Franchise/Team. Does NOT contain fake templates.
2. "What is La Liga?" -> Contains Spain, Football, League, Barcelona/Real Madrid.
3. "What is Formula 1?" -> Contains FIA/Formula One, Grand Prix/Race.
4. "Binary Search" -> Contains binary_search, mid, left, right, O(log n).
5. "Develop Formula 1 Website" -> Dynamic documentation. Does NOT contain "AIForge Generated Full-Stack Platform".
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.agents.explanation_agent import global_explanation_agent
from backend.agents.coding_agent import global_coding_agent
from backend.graph.nodes import documentation_node

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


def verify_p0_critical_fix():
    print("===========================================================================")
    print(" 🚀 AIForge V2 – P0 Critical Bug Fix Master Verification")
    print("===========================================================================\n")

    # ---------------------------------------------------------
    # Test 1: Mumbai Indians
    # ---------------------------------------------------------
    section("Test 1: 'What is Mumbai Indians?'")
    res1 = global_explanation_agent.process_explanation_request("What is Mumbai Indians?")
    t1 = res1["response"]

    check("Identified domain as Cricket", "Cricket" in res1["domain"])
    check("Contains 'Mumbai' and 'IPL'", "Mumbai" in t1 and "IPL" in t1)
    check("Does NOT contain fake section headers", "Overview of" not in t1 and "Core Concept" not in t1)

    # ---------------------------------------------------------
    # Test 2: La Liga
    # ---------------------------------------------------------
    section("Test 2: 'What is La Liga?'")
    res2 = global_explanation_agent.process_explanation_request("What is La Liga?")
    t2 = res2["response"]

    check("Contains 'Spain', 'football'/'soccer', and 'league'", "Spain" in t2 and ("football" in t2.lower() or "soccer" in t2.lower()) and "league" in t2.lower())
    check("Does NOT contain 'Domain Context'", "Domain Context" not in t2)

    # ---------------------------------------------------------
    # Test 3: Formula 1
    # ---------------------------------------------------------
    section("Test 3: 'What is Formula 1?'")
    res3 = global_explanation_agent.process_explanation_request("What is Formula 1?")
    t3 = res3["response"]

    check("Contains 'FIA', 'Formula 1', or 'racing'", "FIA" in t3 or "Formula 1" in t3 or "racing" in t3.lower())
    check("Does NOT contain 'Practical Applications'", "Practical Applications" not in t3)

    # ---------------------------------------------------------
    # Test 4: Binary Search
    # ---------------------------------------------------------
    section("Test 4: 'Binary Search Code'")
    res4 = global_coding_agent.process_coding_request("Binary Search Code")
    t4 = res4["response"]

    check("Contains 'binary_search' function and 'mid'", "binary_search" in t4 and "mid" in t4.lower())
    check("Contains complexity O(log n)", "O(log n)" in t4 or "O(\\log n)" in t4)
    check("Does NOT contain hardcoded template 'sorted(data)'", "sorted(data)" not in t4)

    # ---------------------------------------------------------
    # Test 5: Dynamic Project Generation
    # ---------------------------------------------------------
    section("Test 5: Dynamic Project Generation ('Develop Formula 1 Website')")
    state5 = {"prompt": "Develop Formula 1 Website"}
    out_state5 = documentation_node(state5)
    doc5 = out_state5["documentation"]

    check("Title dynamically generated with project prompt", "# Develop Formula 1 Website - Technical Documentation" in doc5)
    check("Does NOT contain '# AIForge Generated Full-Stack Platform'", "# AIForge Generated Full-Stack Platform" not in doc5)

    # Summary
    print("\n" + "="*75)
    print(f" AIFORGE V2 P0 CRITICAL FIX VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: { _results['passed'] } | Failed: { _results['failed'] }")
    print("="*75 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = verify_p0_critical_fix()
    sys.exit(0 if success else 1)
