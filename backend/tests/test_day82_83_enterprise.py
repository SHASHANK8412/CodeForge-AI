"""
Backend Test Runner for Day 82-83 Enterprise AIForge Self-Improvement & Autonomous Product Builder Verification Suite
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from tests.verify_day82_83_enterprise import main as run_day82_83_tests

if __name__ == "__main__":
    success = run_day82_83_tests()
    if not success:
        print("[FAIL] Day 82-83 Enterprise AIForge Self-Improvement & Product Builder Tests failed!")
        sys.exit(1)
    print("[PASS] All Day 82-83 Enterprise AIForge Self-Improvement & Product Builder Tests passed successfully!")
    sys.exit(0)
