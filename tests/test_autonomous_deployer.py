"""
Day 50 - Root Test Runner for Elite Autonomous Deployment Agent
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from tests.verify_day50_autonomous_deployer import main as run_day50_tests

if __name__ == "__main__":
    success = run_day50_tests()
    if not success:
        sys.exit(1)
    sys.exit(0)
