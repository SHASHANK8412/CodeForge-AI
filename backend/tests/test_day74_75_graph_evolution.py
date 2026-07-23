"""
Backend Test Runner for Day 74-75 Knowledge Graph & Code Evolution Verification Suite
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from tests.verify_day74_75_graph_evolution import main as run_day74_75_tests

if __name__ == "__main__":
    success = run_day74_75_tests()
    if not success:
        print("[FAIL] Day 74-75 Knowledge Graph & Code Evolution Engine Tests failed!")
        sys.exit(1)
    print("[PASS] All Day 74-75 Knowledge Graph & Code Evolution Engine Tests passed successfully!")
    sys.exit(0)
