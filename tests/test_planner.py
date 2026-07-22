"""
Day 42 - Root Test Suite Wrapper for Architecture Planning
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from tests.verify_day42_planner import main as run_day42_tests

if __name__ == "__main__":
    success = run_day42_tests()
    if not success:
        sys.exit(1)
    sys.exit(0)
