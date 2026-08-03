"""
AIForge Real 4-Request Routing Path Proof & End-to-End Verification
====================================================================
Executes 4 distinct requests through the actual backend chat_message API endpoint:

1. REQUEST 1: "Explain Formula 1"
   - Expected: EXPLANATION -> ExplanationAgent (Domain concept explanation, no algorithms)

2. REQUEST 2: "Develop a Formula 1 website"
   - Expected: PROJECT_GENERATION -> Autonomous Software Engineer Pipeline (Requirements, Architect, File Manifest)

3. REQUEST 3: "Solve Two Sum"
   - Expected: DSA_PROBLEM -> CodingAgent / DSASolverAgent (Two Sum Hash Map Algorithm)

4. REQUEST 4: "Why is my React component crashing?"
   - Expected: DEBUGGING -> DebugAgent (AST Diagnosis & Resolution)
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.schemas.chat import ChatMessageRequest
from backend.routes.chat import chat_message

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


async def prove_4_requests():
    print("===========================================================================")
    print(" 🚀 AIForge Real End-to-End Routing Proof Across 4 Distinct Workflows")
    print("===========================================================================\n")

    # --- REQUEST 1: EXPLANATION ---
    req1_prompt = "Explain Formula 1"
    print(f"--- REQUEST 1: '{req1_prompt}' ---")
    res1 = await chat_message(ChatMessageRequest(message=req1_prompt))
    
    intent1 = res1.get("intent")
    agent1 = res1.get("agent")
    text1 = res1.get("response", "")

    print(f"  - Intent Detected:  {intent1}")
    print(f"  - Selected Agent:   {agent1}")
    print(f"  - Model Used:       {res1.get('model')}")
    print(f"  - Response Preview:\n    {text1[:180]}...\n")

    check("REQUEST 1 Intent is EXPLANATION", intent1 == "EXPLANATION")
    check("REQUEST 1 Agent is ExplanationAgent", agent1 == "ExplanationAgent")
    check("REQUEST 1 Response does NOT contain 'def solve_'", "def solve_" not in text1)
    check("REQUEST 1 Response does NOT contain 'result.sort()'", "result.sort()" not in text1)

    # --- REQUEST 2: PROJECT_GENERATION ---
    req2_prompt = "Develop a Formula 1 website"
    print(f"\n--- REQUEST 2: '{req2_prompt}' ---")
    res2 = await chat_message(ChatMessageRequest(message=req2_prompt))
    
    intent2 = res2.get("intent")
    agent2 = res2.get("agent")
    files2 = res2.get("files", {})

    print(f"  - Intent Detected:  {intent2}")
    print(f"  - Selected Agent:   {agent2}")
    print(f"  - Workflow:         Autonomous Software Engineer Pipeline")
    print(f"  - Files Generated:  {len(files2)} Files")
    print(f"  - Manifest Files:   {', '.join(list(files2.keys())[:5])}...\n")

    check("REQUEST 2 Intent is PROJECT_GENERATION", intent2 == "PROJECT_GENERATION")
    check("REQUEST 2 Agent is LangGraph_MultiAgent_Pipeline", agent2 == "LangGraph_MultiAgent_Pipeline")
    check("REQUEST 2 Generated >= 15 Project Files", len(files2) >= 15)

    # --- REQUEST 3: DSA_PROBLEM ---
    req3_prompt = "Solve Two Sum"
    print(f"\n--- REQUEST 3: '{req3_prompt}' ---")
    res3 = await chat_message(ChatMessageRequest(message=req3_prompt))
    
    intent3 = res3.get("intent")
    agent3 = res3.get("agent")
    text3 = res3.get("response", "")

    print(f"  - Intent Detected:  {intent3}")
    print(f"  - Selected Agent:   {agent3}")
    print(f"  - Response Preview:\n    {text3[:180]}...\n")

    check("REQUEST 3 Intent is DSA_PROBLEM", intent3 == "DSA_PROBLEM")
    check("REQUEST 3 Agent is CodingAgent", agent3 == "CodingAgent")
    check("REQUEST 3 Response contains Two Sum algorithm", "two_sum" in text3 or "target - num" in text3 or "seen" in text3)
    check("REQUEST 3 Response does NOT contain fake solve_ algorithm", "def solve_solve_two_sum" not in text3)

    # --- REQUEST 4: DEBUGGING ---
    req4_prompt = "Why is my React component crashing?"
    print(f"\n--- REQUEST 4: '{req4_prompt}' ---")
    res4 = await chat_message(ChatMessageRequest(message=req4_prompt))
    
    intent4 = res4.get("intent")
    agent4 = res4.get("agent")
    text4 = res4.get("response", "")

    print(f"  - Intent Detected:  {intent4}")
    print(f"  - Selected Agent:   {agent4}")
    print(f"  - Response Preview:\n    {text4[:180]}...\n")

    check("REQUEST 4 Intent is DEBUGGING", intent4 == "DEBUGGING")
    check("REQUEST 4 Agent is DebugAgent", agent4 == "DebugAgent")
    check("REQUEST 4 Response contains Debug Diagnosis", "Debug Diagnosis" in text4 or "React Component Crash" in text4 or "stacktrace" in text4)

    # Summary
    print("\n" + "="*75)
    print(f" 4-WORKFLOW ROUTING PROOF SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: { _results['passed'] } | Failed: { _results['failed'] }")
    print("="*75 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = asyncio.run(prove_4_requests())
    sys.exit(0 if success else 1)
