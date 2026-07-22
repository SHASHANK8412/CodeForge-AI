"""
Day 51 - Backend Test Runner for Elite Security Agent Infrastructure
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from tests.verify_day51_elite_security import main as run_day51_tests

if __name__ == "__main__":
    success = run_day51_tests()
    if not success:
        print("[FAIL] Day 51 Elite Security Agent Tests failed!")
        sys.exit(1)
    print("[PASS] All Day 51 Elite Security Agent Tests passed successfully!")
    sys.exit(0)
