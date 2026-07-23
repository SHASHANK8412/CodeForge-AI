"""
Backend Test Runner for Day 88-89 Autonomous AI Company & Self-Evolution Verification Suite
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from tests.verify_day88_89_autonomous_company import main as run_day88_89_tests

if __name__ == "__main__":
    success = run_day88_89_tests()
    if not success:
        print("[FAIL] Day 88-89 Autonomous AI Company & Self-Evolution Tests failed!")
        sys.exit(1)
    print("[PASS] All Day 88-89 Autonomous AI Company & Self-Evolution Tests passed successfully!")
    sys.exit(0)
