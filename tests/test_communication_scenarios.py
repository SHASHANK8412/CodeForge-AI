"""
Day 49 - Root Test Runner for Communication Infrastructure How-to-Test Scenarios
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from tests.verify_day49_scenarios import main as run_scenarios

if __name__ == "__main__":
    success = run_scenarios()
    if not success:
        sys.exit(1)
    sys.exit(0)
