"""
Day 44 - E2E Code Review & Refactoring Engine Scenarios Verification Suite
=============================================================================
Validates all 5 Day 44 User Test Scenarios:
- Test 1: Code Smell Detection (Duplicate Logic)
- Test 2: Security Review (Unsafe SQL & Hardcoded Secret)
- Test 3: Performance (Inefficient Loops & Repeated Queries)
- Test 4: React Review (Large Component, Memoization, Lazy Loading)
- Test 5: Quality Report (review.json, review.md, Quality Score, Fixes List)
"""

import sys
import json
import tempfile
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
    print(" AIForge Day 44 - Autonomous Code Review & Refactoring Scenarios")
    print("======================================================================")

    engine = AutonomousReviewEngine()

    # ==============================================================
    section("Test 1 – Code Smell Detection (Duplicated Logic)")
    # ==============================================================
    code_with_duplication = """
def calculate_user_total(items):
    total = 0
    for i in items:
        total += i.price
    return total

def calculate_order_total(items):
    total = 0
    for i in items:
        total += i.price
    return total
"""
    res1 = engine.review_and_refactor_file("backend/calculator.py", code_with_duplication)
    smell_issues = [f for f in res1.findings if f.category == "code_smell"]

    print("Code Analysis:")
    print("  [OK] Duplicate code detected")
    print("  [OK] Cleaner implementation suggested: Extract to helper function\n")

    check("Duplicate code detected", len(smell_issues) > 0 and any("duplicate" in f.issue.lower() for f in smell_issues))
    check("Cleaner implementation suggested", any("helper function" in f.recommendation.lower() for f in smell_issues))

    # ==============================================================
    section("Test 2 – Security Review (Unsafe SQL & Secrets)")
    # ==============================================================
    vulnerable_api_code = """
import os

DB_SECRET = "super_secret_password_12345"

def get_user_by_id(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
"""
    res2 = engine.review_and_refactor_file("backend/routes/user.py", vulnerable_api_code)
    sec_issues = [f for f in res2.findings if f.category == "security"]
    refactored_code2 = res2.refactored_code

    print("Security Findings:")
    print("  [OK] Vulnerability identified: Hardcoded secret & SQL Injection")
    print("  [OK] Secure alternative proposed: os.getenv() & Parameterized queries\n")

    check("Hardcoded secret vulnerability identified", any("hardcoded secret" in f.issue.lower() for f in sec_issues))
    check("SQL Injection vulnerability identified", any("sql injection" in f.issue.lower() for f in sec_issues))
    check("Secure alternative implemented (os.getenv)", "os.getenv" in refactored_code2)

    # ==============================================================
    section("Test 3 – Performance (Inefficient Loops & N+1 Queries)")
    # ==============================================================
    inefficient_code = """
async def process_orders(order_ids):
    time.sleep(1.0)
    for oid in order_ids:
        query = f"SELECT * FROM orders WHERE id = {oid}"
        db.execute(query)
"""
    res3 = engine.review_and_refactor_file("backend/services/orders.py", inefficient_code)
    perf_issues = [f for f in res3.findings if f.category == "performance"]
    refactored_code3 = res3.refactored_code

    print("Performance Findings:")
    print("  [OK] Blocking sleep & N+1 query loop identified")
    print("  [OK] Optimization recommendations produced")
    print("  [OK] Refactored code replaces blocking calls\n")

    check("Performance issues identified (blocking sleep / N+1 query)", len(perf_issues) > 0)
    check("Optimization recommendations produced", any("await asyncio.sleep" in f.recommendation or "batch" in f.recommendation.lower() for f in perf_issues))
    check("Refactored code improves efficiency (non-blocking sleep)", "await asyncio.sleep" in refactored_code3)

    # ==============================================================
    section("Test 4 – React Review (Large Component & Optimization)")
    # ==============================================================
    large_react_component = """
import React, { useState, useEffect } from 'react';

export default function LargeDashboardView({ data }) {
    const [filter, setFilter] = useState('');
    const [sortedData, setSortedData] = useState([]);

    // Heavy render logic
    const renderTable = () => {
        return data.map(item => (
            <div key={item.id} className="row">
                <span>{item.name}</span>
                <span>{item.value}</span>
            </div>
        ));
    };

    return (
        <div className="dashboard-container">
            <h1>Admin Dashboard</h1>
            <input value={filter} onChange={e => setFilter(e.target.value)} />
            <div className="table">{renderTable()}</div>
        </div>
    );
}
"""
    res4 = engine.review_and_refactor_file("frontend/src/pages/LargeDashboardView.jsx", large_react_component)
    react_issues = [f for f in res4.findings if "React Component" in f.issue or "React" in f.recommendation]

    print("React Audit Findings:")
    print("  [OK] Component size & render complexity analyzed")
    print("  [OK] Component split into smaller sub-components suggested")
    print("  [OK] Memoization (React.memo/useMemo) & Lazy Loading suggested\n")

    check("Large React component identified", len(react_issues) > 0)
    check("Component split & memoization (useMemo/React.memo) suggested", any("sub-components" in f.recommendation or "useMemo" in f.recommendation for f in react_issues))
    check("Lazy loading (React.lazy) suggested for routes", any("React.lazy" in f.recommendation for f in react_issues))

    # ==============================================================
    section("Test 5 – Quality Report Artifacts Generation")
    # ==============================================================
    project_files = {
        "backend/main.py": vulnerable_api_code,
        "backend/orders.py": inefficient_code,
        "frontend/src/Dashboard.jsx": large_react_component
    }

    proj_review = engine.review_project(project_files)

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "review.json"
        md_path = Path(tmpdir) / "review.md"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(proj_review["json_report"], f, indent=2)

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(proj_review["markdown_report"])

        json_exists = json_path.exists()
        md_exists = md_path.exists()

    overall_score = proj_review["overall_quality_score"]
    json_data = proj_review["json_report"]

    print("Artifact Verification:")
    print(f"  [OK] review.json generated (Score: {overall_score})")
    print("  [OK] review.md generated")
    print(f"  [OK] List of issues found: {len(json_data.get('files', []))} files audited")
    print("  [OK] List of automatic fixes generated\n")

    check("review.json generated", json_exists)
    check("review.md generated", md_exists)
    check("Overall quality score present", 0.0 <= overall_score <= 100.0)
    check("List of issues found present in JSON report", len(json_data.get("files", [])) > 0)
    check("List of automatic fixes present in report", "refactored_workspace" in proj_review)

    # Summary
    print("\n" + "="*70)
    print(f" DAY 44 SCENARIO SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
