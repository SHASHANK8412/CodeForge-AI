"""
Backend Test Runner for Day 92 Autonomous Learning & Self-Improving AI Engineer Verification Suite
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from tests.verify_day92_autonomous_learning import main as run_day92_tests

if __name__ == "__main__":
    success = run_day92_tests()
    if not success:
        print("[FAIL] Day 92 Autonomous Learning & Self-Improving AI Engineer Tests failed!")
        sys.exit(1)
    print("[PASS] All Day 92 Autonomous Learning & Self-Improving AI Engineer Tests passed successfully!")
    sys.exit(0)
