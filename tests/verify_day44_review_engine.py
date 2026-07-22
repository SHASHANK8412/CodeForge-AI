"""
Day 44 - Autonomous AI Code Review & Refactoring Engine Verification Suite
=============================================================================
Validates all 10 Requirements:
1. Multi-file type reviewing (Python, JS, SQL, HTML)
2. Code Smell Detection
3. Performance Issue Detection
4. Security Vulnerability Detection
5. Automatic Code Refactoring
6. AST Functionality Preservation
7. Quality Scoring & Letter Grading
8. Markdown and JSON Report Generation
9. Unified Diff Output
10. LangGraph Workflow Integration (Testing -> Reviewer -> Documentation)
"""

import sys
import ast
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.review.autonomous_review_engine import AutonomousReviewEngine

PASS = "[PASS]"
FAIL = "[FAIL]"
_results = {"passed": 0, "failed": 0}


def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def check(name, condition, detail=""):
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


def main():
    print("======================================================================")
    print(" AIForge Day 44 - Autonomous AI Code Review Engine Verification")
    print("======================================================================")

    engine = AutonomousReviewEngine()

    sample_vulnerable_code = """import os
import sys
import time
import math

SECRET_KEY = "super_secret_api_key_12345678"

async def process_user_data(user_id):
    time.sleep(2.0)
    for i in range(10):
        db.query(f"SELECT * FROM users WHERE id = {user_id}")
    return user_id

def overly_long_and_nested_function():
    if True:
        if True:
            if True:
                if True:
                    if True:
                        print("Deep nesting")
"""

    sample_files = {
        "backend/auth.py": sample_vulnerable_code,
        "frontend/src/App.jsx": "import React from 'react';\nexport default function App() { return <div>App</div>; }",
        "database/schema.sql": "CREATE TABLE users (id UUID PRIMARY KEY, email VARCHAR);",
        "public/index.html": "<!DOCTYPE html><html><body><h1>AIForge</h1></body></html>"
    }

    # ==============================================================
    section("Requirement 1 – Review Every Generated File")
    # ==============================================================
    review_output = engine.review_project(sample_files)
    file_results = review_output["file_results"]

    reviewed_filenames = [fr.filename for fr in file_results]
    check("All 4 files across Python, JS, SQL, and HTML reviewed", len(file_results) == 4)
    check("Python, JS, SQL, HTML file types supported", "backend/auth.py" in reviewed_filenames and "frontend/src/App.jsx" in reviewed_filenames)

    # ==============================================================
    section("Requirement 2 – Detect Code Smells")
    # ==============================================================
    auth_review = next(fr for fr in file_results if fr.filename == "backend/auth.py")
    smell_findings = [f for f in auth_review.findings if f.category == "code_smell"]

    check("Code smells detected (unused import / missing type hints / deep nesting)", len(smell_findings) > 0)
    check("Unused import or nesting depth identified", any("Unused import" in f.issue or "nesting" in f.issue.lower() for f in smell_findings))

    # ==============================================================
    section("Requirement 3 – Identify Performance Issues")
    # ==============================================================
    perf_findings = [f for f in auth_review.findings if f.category == "performance"]
    check("Performance issue detected (blocking time.sleep in async def / query in loop)", len(perf_findings) > 0)
    check("Blocking sleep inside async function flagged", any("time.sleep" in f.issue for f in perf_findings))

    # ==============================================================
    section("Requirement 4 – Detect Security Vulnerabilities")
    # ==============================================================
    sec_findings = [f for f in auth_review.findings if f.category == "security"]
    check("Security vulnerabilities detected (hardcoded secret / SQL injection)", len(sec_findings) > 0)
    check("Hardcoded secret key flagged", any("hardcoded secret" in f.issue.lower() for f in sec_findings))

    # ==============================================================
    section("Requirement 5 – Automatic Code Refactoring")
    # ==============================================================
    refactored_auth = auth_review.refactored_code
    check("Hardcoded secret automatically refactored to os.getenv", "os.getenv" in refactored_auth)
    check("Blocking time.sleep refactored to asyncio.sleep", "await asyncio.sleep" in refactored_auth)

    # ==============================================================
    section("Requirement 6 – Preserve Functionality & AST Validity")
    # ==============================================================
    ast_valid = True
    try:
        ast.parse(refactored_auth)
    except Exception:
        ast_valid = False

    check("Refactored code maintains clean AST syntax validity", ast_valid)

    # ==============================================================
    section("Requirement 7 – Generate Quality Scores & Grades")
    # ==============================================================
    score = review_output["overall_quality_score"]
    grade = review_output["grade"]

    check("Overall Quality Score generated (range 0.0 - 100.0)", 0.0 <= score <= 100.0)
    check(f"Letter Grade assigned: {grade}", grade in ["A+", "A", "B", "C", "F"])

    # ==============================================================
    section("Requirement 8 – Produce Markdown and JSON Reports")
    # ==============================================================
    json_report = review_output["json_report"]
    md_report = review_output["markdown_report"]

    check("JSON review report generated", "overall_quality_score" in json_report and "files" in json_report)
    check("Markdown review report generated", "# 🔍 Autonomous AI Code Review" in md_report and "| File |" in md_report)

    # ==============================================================
    section("Requirement 9 – Show Before/After Code Differences")
    # ==============================================================
    diff = auth_review.diff
    check("Unified diff generated showing before/after changes", "--- a/backend/auth.py" in diff and "+++ b/backend/auth.py" in diff)

    # ==============================================================
    section("Requirement 10 – LangGraph Workflow Integration")
    # ==============================================================
    from backend.graph.parallel_workflow import parallel_graph
    from backend.graph.project_workflow import project_graph

    check("LangGraph parallel graph contains reviewer node", "reviewer" in parallel_graph.nodes)
    check("LangGraph project graph contains reviewer node", "reviewer" in project_graph.nodes)

    # Summary
    print("\n" + "="*70)
    print(f" DAY 44 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
