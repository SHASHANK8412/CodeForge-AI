"""
Day 50 - Root Test Runner for How-to-Test Autonomous Deployment Scenarios
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from tests.verify_day50_scenarios import main as run_scenarios

if __name__ == "__main__":
    success = run_scenarios()
    if not success:
        sys.exit(1)
    sys.exit(0)
