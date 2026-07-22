"""
Day 49 - Root Test Runner for Communication Manager Infrastructure
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from tests.verify_day49_communication_manager import main as run_day49_tests

if __name__ == "__main__":
    success = run_day49_tests()
    if not success:
        sys.exit(1)
    sys.exit(0)
