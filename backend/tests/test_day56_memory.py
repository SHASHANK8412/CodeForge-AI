"""
Backend Test Runner for Memory & Knowledge Graph Engine Verification Suite
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from tests.verify_day56_memory import main as run_day56_tests

if __name__ == "__main__":
    success = run_day56_tests()
    if not success:
        print("[FAIL] Day 56 Memory & Knowledge Graph Engine Tests failed!")
        sys.exit(1)
    print("[PASS] All Day 56 Memory & Knowledge Graph Engine Tests passed successfully!")
    sys.exit(0)
