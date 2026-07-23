"""
Backend Test Runner for Day 84-85 Enterprise Sprint Planning & Multi-User Collaboration Verification Suite
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from tests.verify_day84_85_sprint_collaboration import main as run_day84_85_tests

if __name__ == "__main__":
    success = run_day84_85_tests()
    if not success:
        print("[FAIL] Day 84-85 Enterprise Sprint Planning & Multi-User Collaboration Tests failed!")
        sys.exit(1)
    print("[PASS] All Day 84-85 Enterprise Sprint Planning & Multi-User Collaboration Tests passed successfully!")
    sys.exit(0)
