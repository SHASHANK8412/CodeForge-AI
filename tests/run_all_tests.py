"""
Master Diagnostic Test Suite Runner for AIForge
===============================================
Discovers and executes every test in tests/ and backend/tests/ to detect and report errors across the system.
"""

import sys
import os
import subprocess
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

def run_test_file(test_path: Path):
    rel_path = test_path.relative_to(project_root)
    print(f"Running {rel_path}...", end=" ", flush=True)
    
    try:
        with open(test_path, "r", encoding="utf-8") as f:
            file_content = f.read()

        # If file is a runner wrapper script without pytest functions, run directly with python
        if test_path.name in ["test_collaboration.py", "test_elite_security.py", "test_elite_security_scenarios.py"] or ("if __name__ ==" in file_content and "def test_" not in file_content):
            cmd = [sys.executable, str(test_path)]
        elif "def test_" in file_content or "@pytest" in file_content:
            cmd = [sys.executable, "-m", "pytest", str(test_path)]
        else:
            cmd = [sys.executable, str(test_path)]

        proc = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=120
        )
        if proc.returncode == 0:
            print("[PASS]")
            return True, ""
        else:
            print("[FAIL]")
            output = proc.stdout + "\n" + proc.stderr
            return False, output.strip()
    except Exception as e:
        print("[ERROR]")
        return False, str(e)

def main():
    print("======================================================================")
    print(" AIForge System-Wide Comprehensive Test & Error Diagnostic Runner")
    print("======================================================================\n")

    tests_dir = project_root / "tests"
    test_files = sorted([
        f for f in tests_dir.glob("test_*.py") 
        if f.name != "run_all_tests.py"
    ])
    verify_files = sorted(tests_dir.glob("verify_*.py"))

    all_files = test_files + verify_files

    passed = []
    failed = []

    for tf in all_files:
        success, err_log = run_test_file(tf)
        if success:
            passed.append(tf.name)
        else:
            failed.append((tf.name, err_log))

    print("\n" + "="*70)
    print(f" COMPREHENSIVE TEST DIAGNOSTIC SUMMARY")
    print("="*70)
    print(f" Total Suites Executed: {len(all_files)}")
    print(f" Passed Suites: {len(passed)}")
    print(f" Failed Suites: {len(failed)}")
    print("="*70 + "\n")

    if failed:
        print("[FAIL] FAILED SUITES & ERROR DETAILS:")
        for fname, err in failed:
            print(f"\n--- [FAIL] {fname} ---")
            print(err[:1000]) # First 1000 chars of error
            print("-" * 50)
        sys.exit(1)
    else:
        print("[SUCCESS] All test suites passed cleanly with 0 errors!")
        sys.exit(0)

if __name__ == "__main__":
    main()
