"""
AIForge V2 Master Verification Suite: Multi-Domain Explanation Agent & Semantic Relevance Validation
===================================================================================================
Tests multi-domain explanation capabilities:
1. "WHAT IS FORMULA 1" -> Domain: Motorsport (Contains F1, Grand Prix, FIA, Ferrari, Red Bull; NO software jargon)
2. "What is Photosynthesis?" -> Domain: Biology (Contains plants, chlorophyll, sunlight; NO software jargon)
3. "What is Inflation?" -> Domain: Economics (Contains prices, purchasing power, central bank; NO software jargon)
4. "What is Kubernetes?" -> Domain: Cloud Computing (Contains container orchestration, pods)
5. Semantic Validator Rejection -> Rejects software engineering templates for non-tech subjects.
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


def verify_semantic_explanation():
    print("===========================================================================")
    print(" 🚀 AIForge V2 – Multi-Domain Explanation & Semantic Validation Verification")
    print("===========================================================================\n")

    agent = global_explanation_agent

    # ---------------------------------------------------------
    # Scenario 1: Formula 1 Query
    # ---------------------------------------------------------
    section("Scenario 1: Prompt 'WHAT IS FORMULA 1'")
    prompt1 = "WHAT IS FORMULA 1"
    res1 = agent.process_explanation_request(prompt1)
    t1 = res1["response"]

    check("Identified domain as Motorsport", res1["domain"] == "Motorsport")
    check("Semantic Domain Validation Passed", res1["validation_passed"])
    check("Contains 'Formula 1', 'Grand Prix', and 'FIA' domain concepts", "Formula 1" in t1 and "Grand Prix" in t1 and "FIA" in t1)
    check("Contains team references (Ferrari, Red Bull, Mercedes, McLaren)", "Ferrari" in t1 or "Red Bull" in t1 or "Mercedes" in t1)
    check("Does NOT contain out-of-context software engineering jargon (microservices, data structures)", "microservices" not in t1.lower() and "data structures" not in t1.lower())

    # ---------------------------------------------------------
    # Scenario 2: Photosynthesis Query
    # ---------------------------------------------------------
    section("Scenario 2: Prompt 'What is Photosynthesis?'")
    prompt2 = "What is Photosynthesis?"
    res2 = agent.process_explanation_request(prompt2)
    t2 = res2["response"]

    check("Identified domain as Biology", res2["domain"] == "Biology")
    check("Contains biological concepts (chlorophyll, sunlight, oxygen, glucose)", "chlorophyll" in t2.lower() and "sunlight" in t2.lower())
    check("Does NOT contain software engineering template jargon", "microservices" not in t2.lower())

    # ---------------------------------------------------------
    # Scenario 3: Inflation Query
    # ---------------------------------------------------------
    section("Scenario 3: Prompt 'What is Inflation?'")
    prompt3 = "What is Inflation?"
    res3 = agent.process_explanation_request(prompt3)
    t3 = res3["response"]

    check("Identified domain as Economics", res3["domain"] == "Economics")
    check("Contains economic concepts (prices, purchasing power, central banks)", "prices" in t3.lower() and "purchasing power" in t3.lower())
    check("Does NOT contain software engineering template jargon", "data structures" not in t3.lower())

    # ---------------------------------------------------------
    # Scenario 4: Kubernetes Query
    # ---------------------------------------------------------
    section("Scenario 4: Prompt 'What is Kubernetes?'")
    prompt4 = "What is Kubernetes?"
    res4 = agent.process_explanation_request(prompt4)
    t4 = res4["response"]

    check("Identified domain as Cloud Computing", res4["domain"] == "Cloud Computing")
    check("Contains container orchestration concepts (pods, deployments, cluster)", "container" in t4.lower())

    # ---------------------------------------------------------
    # Scenario 5: Semantic Validation Rejection Logic
    # ---------------------------------------------------------
    section("Scenario 5: Semantic Validator Rejection")
    bad_template_out = "Understanding: Formula 1\nThis topic covers fundamental principles in software engineering and microservices."
    val_out = agent.validate_semantic_relevance("WHAT IS FORMULA 1", bad_template_out, "Motorsport")

    check("Semantic Validator rejects software template response for non-software prompt", not val_out["valid"])

    # Summary
    print("\n" + "="*75)
    print(f" AIFORGE V2 SEMANTIC EXPLANATION VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*75 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = verify_semantic_explanation()
    sys.exit(0 if success else 1)
