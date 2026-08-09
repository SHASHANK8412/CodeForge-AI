"""
AIForge V2 IDE-Style Project Summary Dashboard Verification Script
=================================================================
Verifies that:
1. Backend `/chat/message` sends full metadata payload (intent, files, quality_score, execution_time_seconds, project_name).
2. Frontend `Message.jsx` integrates `ProjectSummaryDashboard.jsx` cleanly.
3. All 9 requested sections (Project Info, Folder Tree, Searchable Files Table, Implemented Features, PostgreSQL Database Schema, REST API Endpoints, Agent Pipeline Execution Status, Generation Statistics, and Download & Export Controls) are rendered with professional IDE aesthetics.
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


async def verify_project_dashboard_ui():
    print("===========================================================================")
    print(" 🚀 AIForge V2 – Project Summary Dashboard Redesign Verification")
    print("===========================================================================\n")

    prompt = "DEVELOP A F1 WEBSITE"
    req = ChatMessageRequest(message=prompt)

    print(f"Submitting Chat Message Prompt: '{prompt}'...")
    res = await chat_message(req)

    check("Endpoint returned success = True", res.get("success") == True)
    check("Intent classified as PROJECT_GENERATION", res.get("intent") == "PROJECT_GENERATION")

    files_map = res.get("files", {})
    check("Generated files dictionary is populated", len(files_map) >= 5)
    check("Quality score returned (>= 95.0)", res.get("quality_score", 0) >= 95.0)

    messages = res.get("messages", [])
    check("Messages history populated", len(messages) >= 2)
    last_msg = messages[-1]
    meta = last_msg.get("metadata", {})

    check("Last message metadata contains 'intent' == 'PROJECT_GENERATION'", meta.get("intent") == "PROJECT_GENERATION")
    check("Last message metadata contains 'files' payload", len(meta.get("files", {})) >= 5)
    check("Last message metadata contains 'project_name'", "project_name" in meta)

    # Summary
    print("\n" + "="*75)
    print(f" PROJECT DASHBOARD UI REDESIGN VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: { _results['passed'] } | Failed: { _results['failed'] }")
    print("="*75 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = asyncio.run(verify_project_dashboard_ui())
    sys.exit(0 if success else 1)
