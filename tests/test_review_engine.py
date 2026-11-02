"""
Day 44 - Root Test Runner for Autonomous AI Code Review Engine
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from tests.verify_day44_review_engine import main as run_day44_tests

def test_day44_review_engine():
    # This file only had a __main__ runner, so pytest collected nothing and the checks never ran.
    assert run_day44_tests() is True


if __name__ == "__main__":
    success = run_day44_tests()
    if not success:
        sys.exit(1)
    sys.exit(0)
