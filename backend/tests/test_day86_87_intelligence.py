"""
Backend Test Runner for Day 86-87 Production Intelligence & Autonomous Improvement Verification Suite
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from tests.verify_day86_87_intelligence import main as run_day86_87_tests

if __name__ == "__main__":
    success = run_day86_87_tests()
    if not success:
        print("[FAIL] Day 86-87 Production Intelligence & Autonomous Improvement Tests failed!")
        sys.exit(1)
    print("[PASS] All Day 86-87 Production Intelligence & Autonomous Improvement Tests passed successfully!")
    sys.exit(0)
