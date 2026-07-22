"""
Day 44 - Backend Test Runner for Autonomous AI Code Review & Refactoring Engine
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from tests.verify_day44_review_engine import main as run_day44_tests

if __name__ == "__main__":
    success = run_day44_tests()
    if not success:
        print("[FAIL] Day 44 Review Engine Tests failed!")
        sys.exit(1)
    print("[PASS] All Day 44 Review Engine Tests passed successfully!")
    sys.exit(0)
