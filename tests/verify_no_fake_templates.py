"""
AIForge V2 Master Verification Suite: Complete Elimination of Fake Templates
=============================================================================
Verifies P0 criteria:
1. "What is La Liga?" -> Contains Spain, Football/Soccer, League. Does NOT contain Domain Context, Core Concept, Detailed explanation regarding.
2. "What is Formula 1?" -> Contains FIA, Grand Prix, Race. Does NOT contain Domain Context, Core Concept.
3. "What is Binary Search?" -> Contains sorted array, middle/mid, O(log n). Does NOT contain Domain Context, Core Concept.
4. "What is Python?" -> Contains programming language. Does NOT contain Domain Context, Core Concept.
5. Template Rejection -> Rejects responses containing fake section headers.
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.agents.explanation_agent import global_explanation_agent

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


def verify_no_fake_templates():
    print("===========================================================================")
    print(" 🚀 AIForge V2 – Complete Elimination of Fake Explanation Templates")
    print("===========================================================================\n")

    agent = global_explanation_agent

    # ---------------------------------------------------------
    # Scenario 1: La Liga Query
    # ---------------------------------------------------------
    section("Scenario 1: Prompt 'What is La Liga?'")
    prompt1 = "What is La Liga?"
    res1 = agent.process_explanation_request(prompt1)
    t1 = res1["response"]

    check("Identified domain as Sports / Football", res1["domain"] == "Sports / Football")
    check("Contains 'Spain', 'football'/'soccer', and 'league'", "Spain" in t1 and ("football" in t1.lower() or "soccer" in t1.lower()) and "league" in t1.lower())
    check("Contains famous clubs (Real Madrid, FC Barcelona)", "Real Madrid" in t1 and "Barcelona" in t1)
    check("Does NOT contain 'Domain Context'", "Domain Context" not in t1)
    check("Does NOT contain 'Core Concept'", "Core Concept" not in t1)
    check("Does NOT contain 'Detailed explanation regarding'", "Detailed explanation regarding" not in t1)
    check("Does NOT contain 'Overview of'", "Overview of" not in t1)
    check("Does NOT contain 'Practical Applications'", "Practical Applications" not in t1)

    # ---------------------------------------------------------
    # Scenario 1B: Mumbai Indians Query
    # ---------------------------------------------------------
    section("Scenario 1B: Prompt 'WHAT IS MUMBAI INDIANS'")
    prompt1b = "WHAT IS MUMBAI INDIANS"
    res1b = agent.process_explanation_request(prompt1b)
    t1b = res1b["response"]

    check("Identified domain as Sports / Cricket", res1b["domain"] == "Sports / Cricket")
    check("Contains 'Mumbai' and 'IPL' cricket team details", "Mumbai" in t1b and "IPL" in t1b)
    check("Does NOT contain 'Domain Context' or 'Core Concept'", "Domain Context" not in t1b and "Core Concept" not in t1b)

    # ---------------------------------------------------------
    # Scenario 1C: Chennai Super Kings Query
    # ---------------------------------------------------------
    section("Scenario 1C: Prompt 'WHAT IS CHENNAI SUPER KINGS'")
    prompt1c = "WHAT IS CHENNAI SUPER KINGS"
    res1c = agent.process_explanation_request(prompt1c)
    t1c = res1c["response"]

    check("Identified domain as Sports / Cricket", res1c["domain"] == "Sports / Cricket")
    check("Contains 'Chennai' and 'IPL' cricket team details", "Chennai" in t1c and "IPL" in t1c)
    check("Does NOT contain 'Comprehensive answer for' or 'Fundamental explanation'", "Comprehensive answer for" not in t1c and "Fundamental explanation" not in t1c)

    # ---------------------------------------------------------
    # Scenario 2: Formula 1 Query
    # ---------------------------------------------------------
    section("Scenario 2: Prompt 'What is Formula 1?'")
    prompt2 = "What is Formula 1?"
    res2 = agent.process_explanation_request(prompt2)
    t2 = res2["response"]

    check("Contains 'FIA', 'Formula One', or 'racing'", "FIA" in t2 or "Formula One" in t2 or "racing" in t2.lower())
    check("Does NOT contain 'Domain Context' or 'Core Concept'", "Domain Context" not in t2 and "Core Concept" not in t2)

    # ---------------------------------------------------------
    # Scenario 3: Binary Search Query
    # ---------------------------------------------------------
    section("Scenario 3: Prompt 'What is Binary Search?'")
    prompt3 = "What is Binary Search?"
    res3 = agent.process_explanation_request(prompt3)
    t3 = res3["response"]

    check("Contains 'sorted', 'middle'/'mid', and 'O(log n)'", "sorted" in t3.lower() and ("middle" in t3.lower() or "mid" in t3.lower()) and "O(\\log n)" in t3)
    check("Does NOT contain 'Domain Context' or 'Core Concept'", "Domain Context" not in t3 and "Core Concept" not in t3)

    # ---------------------------------------------------------
    # Scenario 4: Python Query
    # ---------------------------------------------------------
    section("Scenario 4: Prompt 'What is Python?'")
    prompt4 = "What is Python?"
    res4 = agent.process_explanation_request(prompt4)
    t4 = res4["response"]

    check("Contains 'programming language'", "programming language" in t4.lower())
    check("Does NOT contain 'Domain Context' or 'Core Concept'", "Domain Context" not in t4 and "Core Concept" not in t4)

    # ---------------------------------------------------------
    # Scenario 5: Template Rejection Test
    # ---------------------------------------------------------
    section("Scenario 5: Fake Template Rejection Logic")
    fake_hdr_text = "## Overview of What is La Liga\n### Core Concept\nDetailed explanation regarding La Liga.\n### Domain Context"
    val_check = agent.validate_semantic_response("What is La Liga?", fake_hdr_text, "Sports / Football")

    check("Validator rejects output containing fake template header", not val_check["valid"])

    # Summary
    print("\n" + "="*75)
    print(f" AIFORGE V2 NO FAKE TEMPLATES VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: { _results['passed'] } | Failed: { _results['failed'] }")
    print("="*75 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = verify_no_fake_templates()
    sys.exit(0 if success else 1)
