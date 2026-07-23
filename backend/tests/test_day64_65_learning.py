"""
Backend Test Runner for Day 64-65 Continuous Learning & Pattern Mining Verification Suite
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from tests.verify_day64_65_learning import main as run_day64_65_tests

if __name__ == "__main__":
    success = run_day64_65_tests()
    if not success:
        print("[FAIL] Day 64-65 Continuous Learning & Pattern Mining Tests failed!")
        sys.exit(1)
    print("[PASS] All Day 64-65 Continuous Learning & Pattern Mining Tests passed successfully!")
    sys.exit(0)
