"""
Backend Test Runner for Day 81 Autonomous AI Dev Team Collaboration & Sprint Execution Verification Suite
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from tests.verify_day81_sprint import main as run_day81_tests

if __name__ == "__main__":
    success = run_day81_tests()
    if not success:
        print("[FAIL] Day 81 Autonomous AI Dev Team Collaboration & Sprint Execution Tests failed!")
        sys.exit(1)
    print("[PASS] All Day 81 Autonomous AI Dev Team Collaboration & Sprint Execution Tests passed successfully!")
    sys.exit(0)
