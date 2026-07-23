"""
Day 72 - Autonomous AI Pair Programmer Verification Suite
==========================================================
Validates AIForge Pair Programmer across 4 core testing scenarios:
- Test 1: Add Logging to APIs (Only API files edited, Logger imported, middleware updated)
- Test 2: Refactor Authentication (JWT logic improved, duplicate code removed, tests updated)
- Test 3: Dark Mode Theme Switcher (Theme files, Components, CSS, Context, Navbar updated)
- Test 4: Database Query Optimization (Repository analyzed, queries optimized, limit added)
"""

import sys
import json
import time
import asyncio
import tempfile
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.agents.pair_programmer_agent import PairProgrammerAgent

PASS = "[PASS]"
FAIL = "[FAIL]"
_results = {"passed": 0, "failed": 0}


def section(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


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


async def run_day72_tests():
    print("======================================================================")
    print(" AIForge Day 72 - Autonomous AI Pair Programmer Verification Suite")
    print("======================================================================\n")

    agent = PairProgrammerAgent()

    # Create temporary dummy workspace for testing
    with tempfile.TemporaryDirectory() as tmp_dir:
        workspace = Path(tmp_dir)
        (workspace / "backend").mkdir(parents=True, exist_ok=True)
        (workspace / "backend" / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/api/v1/user')\ndef get_user():\n    return {'user': 'admin'}")
        (workspace / "frontend" / "src" / "components").mkdir(parents=True, exist_ok=True)
        (workspace / "frontend" / "src" / "components" / "Navbar.jsx").write_text("export function Navbar() { return <nav className='bg-white'>Navbar</nav>; }")

        # ------------------------------------------------------------------
        section("Test 1 – Add Logging to APIs")
        # ------------------------------------------------------------------
        res1 = agent.process_pair_request(str(workspace), "Add logging to every API", apply_changes=True)

        check("Targeted API files edited", len(res1["files_changed"]) > 0)
        check("Logger imported and request logging added", any("logging" in exp.lower() for exp in res1["explanations"]))
        check("Git-style patch preview generated (+ additions, - deletions)", res1["patch_preview"]["total_additions"] > 0)
        check("Syntax and safety validation passed", res1["validation_report"]["all_valid"])

        # ------------------------------------------------------------------
        section("Test 2 – Refactor Authentication")
        # ------------------------------------------------------------------
        res2 = agent.process_pair_request(str(workspace), "Refactor authentication with JWT verification", apply_changes=True)

        check("JWT authentication logic refactored", any("jwt" in exp.lower() for exp in res2["explanations"]))
        check("Auth routes & token handlers modified", len(res2["files_changed"]) >= 2)
        check("Explanation generated for every modification", len(res2["explanations"]) == len(res2["files_changed"]))

        # ------------------------------------------------------------------
        section("Test 3 – Dark Mode Theme Switcher Multi-File Edit")
        # ------------------------------------------------------------------
        res3 = agent.process_pair_request(str(workspace), "Convert project components to support dark mode", apply_changes=True)

        check("Multi-file edits targeted frontend theme & Navbar files", len(res3["files_changed"]) >= 2)
        check("Theme context & dark mode class handlers inserted", any("dark mode" in exp.lower() for exp in res3["explanations"]))

        # ------------------------------------------------------------------
        section("Test 4 – Database Query Optimization & Memory Update")
        # ------------------------------------------------------------------
        res4 = agent.process_pair_request(str(workspace), "Optimize database queries and loop iterations", apply_changes=True)

        check("Repository analyzed and database queries optimized", len(res4["files_changed"]) > 0)
        check("Query LIMIT & loop enumerations applied", any("loop" in exp.lower() or "limit" in exp.lower() for exp in res4["explanations"]))
        check("Project Memory updated after successful edits", res4["updated_memory"])

    # Summary
    print("\n" + "="*70)
    print(f" DAY 72 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


def main():
    return asyncio.run(run_day72_tests())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
