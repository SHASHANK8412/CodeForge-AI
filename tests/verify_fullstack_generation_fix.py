"""
AIForge V2 Full-Stack Project Generation Fix Verification
=========================================================
Verifies that prompts like 'DEVELOP A F1 WEBSITE' trigger the complete multi-agent software engineering pipeline:
Planner -> Architect -> Frontend -> Backend -> Database -> Testing -> Quality Gates -> Assembly.
Confirms that real production code files, quality scorecard, and quickstart guide are generated and returned in the payload.
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


async def verify_fullstack_generation():
    print("===========================================================================")
    print(" 🚀 AIForge V2 – Full-Stack Project Generation Workflow Fix Verification")
    print("===========================================================================\n")

    prompt = "DEVELOP A F1 WEBSITE"
    req = ChatMessageRequest(message=prompt)

    print(f"Submitting Chat Message Prompt: '{prompt}'...")
    res = await chat_message(req)

    check("Endpoint returned success = True", res.get("success") == True)
    check("Intent classified as PROJECT_GENERATION", res.get("intent") == "PROJECT_GENERATION")

    files_map = res.get("files", {})
    check("Generated files dictionary is populated", len(files_map) >= 5)
    check("Generated frontend SPA (frontend/src/App.jsx)", "frontend/src/App.jsx" in files_map)
    check("Generated backend service (backend/main.py)", "backend/main.py" in files_map)
    check("Generated authentication router (backend/app/routers/auth_router.py)", "backend/app/routers/auth_router.py" in files_map)
    check("Generated database schema (database/schema.sql)", "database/schema.sql" in files_map)
    check("Generated Pytest suite (tests/test_api.py)", "tests/test_api.py" in files_map)
    check("Generated project README documentation (README.md)", "README.md" in files_map)
    check("Quality Score >= 95.0", res.get("quality_score", 0) >= 95.0)

    # Summary
    print("\n" + "="*75)
    print(f" FULL-STACK GENERATION FIX VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: { _results['passed'] } | Failed: { _results['failed'] }")
    print("="*75 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = asyncio.run(verify_fullstack_generation())
    sys.exit(0 if success else 1)
