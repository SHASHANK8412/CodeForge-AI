"""
Backend Test Runner for Day 78-79 Repository Intelligence & Evolution Verification Suite
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from tests.verify_day78_79_repo_evolution import main as run_day78_79_tests

if __name__ == "__main__":
    success = run_day78_79_tests()
    if not success:
        print("[FAIL] Day 78-79 Repository Intelligence & Evolution Tests failed!")
        sys.exit(1)
    print("[PASS] All Day 78-79 Repository Intelligence & Evolution Tests passed successfully!")
    sys.exit(0)
