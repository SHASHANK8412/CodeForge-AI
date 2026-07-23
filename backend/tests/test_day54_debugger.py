"""
Day 54 - Backend Test Runner for Autonomous Debugger Agent Verification Suite
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from tests.verify_day54_debugger import main as run_day54_tests

if __name__ == "__main__":
    success = run_day54_tests()
    if not success:
        print("[FAIL] Day 54 Autonomous Debugger Agent Tests failed!")
        sys.exit(1)
    print("[PASS] All Day 54 Autonomous Debugger Agent Tests passed successfully!")
    sys.exit(0)
