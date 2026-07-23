"""
Backend Test Runner for Day 76-77 Project Intelligence & Prompt Optimizer Verification Suite
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from tests.verify_day76_77_learning_optimizer import main as run_day76_77_tests

if __name__ == "__main__":
    success = run_day76_77_tests()
    if not success:
        print("[FAIL] Day 76-77 Project Intelligence & Prompt Optimizer Tests failed!")
        sys.exit(1)
    print("[PASS] All Day 76-77 Project Intelligence & Prompt Optimizer Tests passed successfully!")
    sys.exit(0)
