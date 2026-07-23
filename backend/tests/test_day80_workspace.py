"""
Backend Test Runner for Day 80 Autonomous Multi-Project Workspace Verification Suite
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from tests.verify_day80_workspace import main as run_day80_tests

if __name__ == "__main__":
    success = run_day80_tests()
    if not success:
        print("[FAIL] Day 80 Autonomous Multi-Project Workspace Tests failed!")
        sys.exit(1)
    print("[PASS] All Day 80 Autonomous Multi-Project Workspace Tests passed successfully!")
    sys.exit(0)
