"""
Day 51 - Root Test Runner for Elite Security Agent Infrastructure
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from tests.verify_day51_elite_security import main as run_day51_tests

def test_day51_elite_security():
    # This file only had a __main__ runner, so pytest collected nothing and the checks never ran.
    assert run_day51_tests() is True


if __name__ == "__main__":
    success = run_day51_tests()
    if not success:
        sys.exit(1)
    sys.exit(0)
