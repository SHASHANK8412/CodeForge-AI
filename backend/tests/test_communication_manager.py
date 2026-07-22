"""
Day 49 - Backend Test Runner for Communication Manager Infrastructure
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from tests.verify_day49_communication_manager import main as run_day49_tests

if __name__ == "__main__":
    success = run_day49_tests()
    if not success:
        print("[FAIL] Day 49 Communication Manager Tests failed!")
        sys.exit(1)
    print("[PASS] All Day 49 Communication Manager Tests passed successfully!")
    sys.exit(0)
