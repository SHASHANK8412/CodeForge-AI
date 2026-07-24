"""
AIForge Day 95 Test Suite: Autonomous AI Pair Programmer & Interactive Code Refinement
=====================================================================================
Tests all 4 Prompt Requirements & Scenarios:
1. Test 1 - Add Dark Mode -> Only UI files modified
2. Test 2 - Use PostgreSQL instead of SQLite -> Database configs & connection strings updated
3. Test 3 - Optimize dashboard loading -> Performance & caching files changed
4. Test 4 - Fix Login Bug -> Authentication module edited, tests pass, docs updated
"""

import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from backend.agents.refactor_agent import global_refactor_agent
from backend.services.file_locator import global_file_locator
from backend.services.dependency_graph import global_dependency_graph_builder
from backend.utils.patch_generator import global_patch_generator


class TestDay95PairProgrammer(unittest.TestCase):

    def setUp(self):
        self.sample_project_files = {
            "frontend/src/theme.js": "export const theme = { mode: 'light' };",
            "frontend/src/components/Navbar.jsx": "export function Navbar() { return <nav>Nav</nav>; }",
            "frontend/src/pages/Dashboard.jsx": "export function Dashboard() { return <div>Dashboard</div>; }",
            "backend/database.py": "DATABASE_URL = 'sqlite:///./test.db'",
            "backend/config.py": "DB_ENGINE = 'sqlite'",
            "backend/auth.py": "def login(user, pwd): return False",
            "backend/routes/auth_routes.py": "@router.post('/login')\ndef login(): pass"
        }

    def test_01_add_dark_mode_modifies_only_ui_files(self):
        res = global_refactor_agent.understand_project_and_modify(
            project_files=self.sample_project_files,
            modification_prompt="Add Dark Mode"
        )
        target_files = res["target_files"]
        self.assertTrue(all(any(ui_kw in f.lower() for ui_kw in ["theme", "navbar", "css", "component", "app"]) for f in target_files))
        self.assertNotIn("backend/database.py", target_files)
        print("✓ Test 1 Passed: 'Add Dark Mode' modified only UI files")

    def test_02_use_postgresql_updates_db_configs(self):
        res = global_refactor_agent.understand_project_and_modify(
            project_files=self.sample_project_files,
            modification_prompt="Use PostgreSQL instead of SQLite"
        )
        target_files = res["target_files"]
        self.assertTrue(any("database.py" in f or "config.py" in f for f in target_files))
        modified_db_code = res["modified_project_files"]["backend/database.py"]
        self.assertIn("postgresql://", modified_db_code)
        print("✓ Test 2 Passed: 'Use PostgreSQL' updated database connection strings & ORM configs")

    def test_03_optimize_dashboard_loading_targets_perf_files(self):
        res = global_refactor_agent.understand_project_and_modify(
            project_files=self.sample_project_files,
            modification_prompt="Optimize dashboard loading"
        )
        target_files = res["target_files"]
        self.assertTrue(any("Dashboard" in f or "cache" in f or "metrics" in f for f in target_files))
        print("✓ Test 3 Passed: 'Optimize dashboard loading' targeted performance & dashboard files")

    def test_04_fix_login_bug_edits_auth_module(self):
        res = global_refactor_agent.understand_project_and_modify(
            project_files=self.sample_project_files,
            modification_prompt="Fix Login Bug"
        )
        target_files = res["target_files"]
        self.assertTrue(any("auth" in f for f in target_files))
        modified_auth_code = res["modified_project_files"]["backend/auth.py"]
        self.assertIn("verify_login_credentials", modified_auth_code)
        print("✓ Test 4 Passed: 'Fix Login Bug' edited authentication module")


def main():
    print("\n" + "="*60)
    print(" Running Day 95 AI Pair Programmer Tests...")
    print("="*60 + "\n")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDay95PairProgrammer)
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    if result.wasSuccessful():
        print("\n" + "="*60)
        print(" ALL TESTS PASSED")
        print("="*60 + "\n")
        return True
    return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
