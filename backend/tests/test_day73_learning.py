"""
Backend Test Runner for Day 73 Autonomous Learning & Self-Improvement Verification Suite
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from tests.verify_day73_learning import main as run_day73_tests

if __name__ == "__main__":
    success = run_day73_tests()
    if not success:
        print("[FAIL] Day 73 Autonomous Learning Engine Tests failed!")
        sys.exit(1)
    print("[PASS] All Day 73 Autonomous Learning Engine Tests passed successfully!")
    sys.exit(0)
