"""
Day 51 - Backend Test Runner for How-to-Test Insecure Project Verification Suite
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from tests.verify_day51_scenarios import main as run_scenarios

if __name__ == "__main__":
    success = run_scenarios()
    if not success:
        print("[FAIL] Day 51 Insecure Project Scenarios failed!")
        sys.exit(1)
    print("[PASS] All Day 51 Insecure Project Scenarios passed successfully!")
    sys.exit(0)
