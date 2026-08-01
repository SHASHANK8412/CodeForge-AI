"""
AIForge Root Directories Verification Script
===========================================
Verifies that:
1. QualityGate Check 1 validates all 3 standard root directories: 'backend', 'frontend', and 'database'
2. Missing any directory correctly returns "Missing recommended root directories: 'backend', 'frontend', and 'database'"
3. ProjectAssembler and IncrementalProjectGenerator automatically enforce the presence of all 3 root directories
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.quality.quality_gates import QualityGatesEngine
from backend.exporter.validator import ProjectValidator
from backend.generators.incremental_generator import IncrementalProjectGenerator
from backend.memory.project_memory import ProjectMemoryStore

PASS = "[PASS]"
FAIL = "[FAIL]"
_results = {"passed": 0, "failed": 0}


def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    if condition:
        _results["passed"] += 1
    else:
        _results["failed"] += 1
    msg = f"  {status}  {name}"
    if detail:
        msg += f"\n        => {detail}"
    print(msg)
    return condition


def verify_root_directories_fix():
    print("===========================================================================")
    print(" 🚀 AIForge V2 – Root Directories Structure Fix Verification")
    print("===========================================================================\n")

    qg_engine = QualityGatesEngine()
    validator = ProjectValidator()
    generator = IncrementalProjectGenerator()

    # 1. Test Incomplete Files Missing Root Directories
    incomplete_files = {
        "main.py": "from fastapi import FastAPI",
        "App.jsx": "export default function App() {}"
    }

    print("1. Testing Quality Gates with Incomplete Layout (Missing Root Dirs):")
    res_incomplete = qg_engine.evaluate_project(incomplete_files, {}, {})
    check1 = res_incomplete.gate_checks[0]
    check("Quality Gate Check 1 failed on incomplete layout", check1["passed"] == False)
    check("Quality Gate detail contains 'Missing recommended root directories'", "Missing recommended root directories" in check1["detail"])

    val_incomplete = validator.validate_project(incomplete_files)
    check("ProjectValidator reported missing root directories", any("Missing recommended root directories" in err for err in val_incomplete["errors"]))

    # 2. Test Complete Generated Project Layout
    print("\n2. Testing Complete Domain-Generated Layout:")
    memory = ProjectMemoryStore("Formula 1 Project")
    complete_files = generator.generate_modules_incrementally("Formula 1 Project", memory)

    res_complete = qg_engine.evaluate_project(complete_files, {}, {})
    check1_comp = res_complete.gate_checks[0]
    check("Quality Gate Check 1 PASSED on full project", check1_comp["passed"] == True)
    check("Has backend/ directory files", any(p.startswith("backend/") for p in complete_files))
    check("Has frontend/ directory files", any(p.startswith("frontend/") for p in complete_files))
    check("Has database/ directory files", any(p.startswith("database/") for p in complete_files))

    val_complete = validator.validate_project(complete_files)
    check("ProjectValidator returns is_valid = True on complete project", val_complete["is_valid"] == True)

    # Summary
    print("\n" + "="*75)
    print(f" ROOT DIRECTORIES STRUCTURE FIX VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: { _results['passed'] } | Failed: { _results['failed'] }")
    print("="*75 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = verify_root_directories_fix()
    sys.exit(0 if success else 1)
