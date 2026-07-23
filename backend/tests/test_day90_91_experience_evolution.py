"""
Backend Test Runner for Day 90-91 Experience Learning Engine & AI Self-Evolution Verification Suite
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from tests.verify_day90_91_experience_evolution import main as run_day90_91_tests

if __name__ == "__main__":
    success = run_day90_91_tests()
    if not success:
        print("[FAIL] Day 90-91 Experience Learning Engine & Self-Evolution Tests failed!")
        sys.exit(1)
    print("[PASS] All Day 90-91 Experience Learning Engine & Self-Evolution Tests passed successfully!")
    sys.exit(0)
