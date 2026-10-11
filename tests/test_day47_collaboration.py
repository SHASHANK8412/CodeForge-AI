"""
Day 47 - Root Test Runner for Collaborative Multi-Agent System
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from tests.verify_day47_collaboration import main as run_day47_tests

def test_day47_collaboration():
    # This file only had a __main__ runner, so pytest collected nothing and the checks never ran.
    assert run_day47_tests() is True


if __name__ == "__main__":
    success = run_day47_tests()
    if not success:
        sys.exit(1)
    sys.exit(0)
