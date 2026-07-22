"""
Day 43 - Root Test Suite Wrapper for Collaborative Multi-Agent Platform
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from tests.verify_day43_collaboration import main as run_day43_tests

if __name__ == "__main__":
    success = run_day43_tests()
    if not success:
        sys.exit(1)
    sys.exit(0)
