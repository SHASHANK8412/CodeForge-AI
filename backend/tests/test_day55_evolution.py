"""
Backend Test Runner for Continuous Learning & Self-Evolution Verification Suite
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from tests.verify_day55_evolution import main as run_day55_tests

if __name__ == "__main__":
    success = run_day55_tests()
    if not success:
        print("[FAIL] Day 55 Continuous Learning & Self-Evolution Tests failed!")
        sys.exit(1)
    print("[PASS] All Day 55 Continuous Learning & Self-Evolution Tests passed successfully!")
    sys.exit(0)
