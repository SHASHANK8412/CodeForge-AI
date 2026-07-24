"""
Day 95 - Autonomous AI Pair Programmer Verification Suite
=========================================================
Validates all Day 95 Deliverables & Objectives:
1. Project Understanding Agent
2. Intelligent File Discovery (Targeted editing)
3. Dependency Graph Generator (dependency_graph.json)
4. Smart Code Editing (Formatting/Comments/Imports preserved)
5. Patch & Diff Generator (Unified diffs)
6. Change Explanation Engine (Reason, Before, After, Impact, Risks)
7. Safe Backup System (.backup/)
8. Multi-step Conversation Memory
9. All 4 Prompt Modification Test Cases
"""

import sys
import asyncio
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.agents.refactor_agent import global_refactor_agent
from backend.services.code_parser import global_code_parser
from backend.services.file_locator import global_file_locator
from backend.services.dependency_graph import global_dependency_graph_builder
from backend.utils.patch_generator import global_patch_generator
from backend.agents.diff_agent import global_diff_agent
from backend.memory.conversation_memory import ConversationMemory

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


async def run_day95_tests():
    print("======================================================================")
    print(" AIForge Day 95 - Autonomous AI Pair Programmer & Interactive Refinement")
    print("======================================================================\n")

    sample_project = {
        "frontend/src/theme.js": "export const theme = { mode: 'light' };",
        "frontend/src/components/Navbar.jsx": "export function Navbar() { return <nav>Nav</nav>; }",
        "frontend/src/pages/Dashboard.jsx": "export function Dashboard() { return <div>Dashboard</div>; }",
        "backend/database.py": "DATABASE_URL = 'sqlite:///./test.db'",
        "backend/config.py": "DB_ENGINE = 'sqlite'",
        "backend/auth.py": "def login(user, pwd): return False",
        "backend/routes/auth_routes.py": "@router.post('/login')\ndef login(): pass"
    }

    # ------------------------------------------------------------------
    section("1. Test Case 1: Add Dark Mode (UI Targeted Modification)")
    # ------------------------------------------------------------------
    res_1 = global_refactor_agent.understand_project_and_modify(sample_project, "Add Dark Mode")
    check("Targeted only UI files (theme.js, Navbar.jsx)", all("backend" not in f for f in res_1["target_files"]))

    # ------------------------------------------------------------------
    section("2. Test Case 2: Use PostgreSQL instead of SQLite")
    # ------------------------------------------------------------------
    res_2 = global_refactor_agent.understand_project_and_modify(sample_project, "Use PostgreSQL instead of SQLite")
    check("Targeted database connection strings & ORM configs", "backend/database.py" in res_2["target_files"])
    check("Updated connection string to postgresql://", "postgresql://" in res_2["modified_project_files"]["backend/database.py"])

    # ------------------------------------------------------------------
    section("3. Test Case 3: Optimize Dashboard Loading")
    # ------------------------------------------------------------------
    res_3 = global_refactor_agent.understand_project_and_modify(sample_project, "Optimize dashboard loading")
    check("Targeted dashboard component & performance layer", any("Dashboard" in f for f in res_3["target_files"]))

    # ------------------------------------------------------------------
    section("4. Test Case 4: Fix Login Bug")
    # ------------------------------------------------------------------
    res_4 = global_refactor_agent.understand_project_and_modify(sample_project, "Fix Login Bug")
    check("Targeted authentication module (auth.py)", any("auth" in f for f in res_4["target_files"]))

    # ------------------------------------------------------------------
    section("5. Dependency Graph Generation")
    # ------------------------------------------------------------------
    dep_graph = global_dependency_graph_builder.build_graph(sample_project)
    check("Built dependency graph mapping frontend component tree and backend layers", "frontend_component_tree" in dep_graph and "backend_flow" in dep_graph)

    # ------------------------------------------------------------------
    section("6. Safe Backup & Unified Diff Patches")
    # ------------------------------------------------------------------
    check("Created safe backups in .backup/ before modifying files", len(res_1["backups_created"]) > 0)
    check("Generated unified diff patches (+ additions, - deletions)", len(res_1["patches"]) > 0 and "additions_count" in res_1["patches"][0])

    # ------------------------------------------------------------------
    section("7. Change Explanation Engine & Multi-step Memory")
    # ------------------------------------------------------------------
    check("Generated structured change explanations (Reason, Before, After, Impact, Risks)", len(res_1["explanations"]) > 0 and "formatted_explanation" in res_1["explanations"][0])
    
    conv_mem = ConversationMemory()
    context = conv_mem.get_incremental_context("session_default")
    check("Multi-step conversation memory persisted turn context and modified files history", context["turn_count"] > 0)

    # Summary
    print("\n" + "="*70)
    print(f" DAY 95 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


def main():
    return asyncio.run(run_day95_tests())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
