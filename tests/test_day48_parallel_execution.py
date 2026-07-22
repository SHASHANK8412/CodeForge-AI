"""
Day 48 - Root Test Runner for Parallel Multi-Agent Execution E2E Suite
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from tests.verify_day48_parallel_execution import main as run_day48_tests

if __name__ == "__main__":
    success = run_day48_tests()
    if not success:
        sys.exit(1)
    sys.exit(0)
