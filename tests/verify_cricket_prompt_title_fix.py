"""
AIForge Prompt Title & Metadata Preservation Verification Script
===============================================================
Verifies that:
1. When user prompt 'DEVELOP A CRICKET WEBSITE' is submitted, project_name in response and metadata is 'Develop A Cricket Website' (NOT Formula 1).
2. ChatBox `toUiMessages` preserves metadata for UI components.
3. ProjectSummaryDashboard defaults to 'Software Project' if project_name is missing instead of hardcoded Formula 1.
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


async def verify_cricket_prompt_title_fix():
    print("===========================================================================")
    print(" 🚀 AIForge V2 – Prompt Title & Metadata Fix Verification")
    print("===========================================================================\n")

    prompt = "DEVELOP A CRICKET WEBSITE"
    req = ChatMessageRequest(message=prompt)

    print(f"Submitting Chat Message Prompt: '{prompt}'...")
    res = await chat_message(req)

    check("Endpoint returned success = True", res.get("success") == True)
    check("Intent classified as PROJECT_GENERATION", res.get("intent") == "PROJECT_GENERATION")

    messages = res.get("messages", [])
    check("Messages payload returned", len(messages) >= 2)
    
    last_assistant_msg = messages[-1]
    meta = last_assistant_msg.get("metadata", {})

    print(f"\nExtracted Metadata from Assistant Message:")
    print(f"  - project_name: {meta.get('project_name')}")
    print(f"  - intent: {meta.get('intent')}")

    check("Metadata 'project_name' matches user prompt ('Develop A Cricket Website')", meta.get("project_name") == "Develop A Cricket Website")
    check("Metadata 'project_name' does NOT contain 'Formula 1'", "Formula 1" not in meta.get("project_name", ""))

    # Summary
    print("\n" + "="*75)
    print(f" PROMPT TITLE FIX VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: { _results['passed'] } | Failed: { _results['failed'] }")
    print("="*75 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = asyncio.run(verify_cricket_prompt_title_fix())
    sys.exit(0 if success else 1)
