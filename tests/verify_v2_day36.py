"""
AIForge V2 Day 36 Verification Suite
=====================================
End-to-end verification script for AIForge V2 Day 36 deliverables:
1. Static Code Inspection & Maintainability Reporting
2. Software Code Metrics Computation & Technical Debt Estimation
3. OWASP Security Vulnerability Scanner
4. Dependency Tree & Package Vulnerability Auditor
5. Enterprise Compliance Checker (OWASP, REST API, GDPR, Coding Guidelines)
6. Automated Refactoring Suggestion Engine
7. AIForge Project Certification Engine (Grade A+, Deployment Ready)
8. Persistent Quality Logs & Quality Dashboard REST APIs
"""

import sys
import asyncio
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.quality.static_analyzer import global_static_code_analyzer
from backend.quality.code_metrics import global_code_metrics_engine
from backend.quality.security_scanner import global_security_scanner
from backend.quality.dependency_scanner import global_dependency_scanner
from backend.quality.compliance_checker import global_compliance_checker
from backend.quality.certification import global_certification_engine

PASS = "[PASS]"
FAIL = "[FAIL]"
_results = {"passed": 0, "failed": 0}


def section(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


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


def run_v2_day36_verification():
    print("======================================================================")
    print(" 🛡️ AIForge V2 – Day 36 Autonomous Quality & Security Verification")
    print("======================================================================\n")

    section("1. Static Code Analysis & Issue Inspection")
    static_rep = global_static_code_analyzer.analyze_project(project_path="src/")
    check("Inspected code complexity & detected unused imports/issues", static_rep["maintainability"] == "Good" and len(static_rep["detected_issues"]) >= 3)

    section("2. Code Metrics & Technical Debt Engine")
    metrics = global_code_metrics_engine.calculate_metrics(project_name="Ecommerce API")
    check("Calculated Cyclomatic Complexity, Coverage & Technical Debt", metrics["maintainability_index"] > 80.0 and metrics["code_coverage_pct"] > 90.0)

    section("3. OWASP Security Vulnerability Scanner")
    sec_rep = global_security_scanner.scan_project(project_path="src/")
    check("Identified OWASP security vulnerabilities & recommendations", sec_rep["security_score"] >= 90 and len(sec_rep["vulnerabilities"]) >= 2)

    section("4. Dependency Scanner & Vulnerability Audit")
    dep_rep = global_dependency_scanner.scan_dependencies()
    check("Audited package dependencies & versions", dep_rep["dependency_health_score"] >= 90 and len(dep_rep["packages"]) == 3)

    section("5. Enterprise Compliance Checker")
    comp_rep = global_compliance_checker.check_compliance(project_name="Ecommerce API")
    check("Validated compliance with OWASP, REST, GDPR & style guidelines", comp_rep["overall_compliance_score"] >= 90 and comp_rep["compliance_status"] == "COMPLIANT")

    section("6. Automated Refactoring Recommendations")
    refactor_recs = global_certification_engine.generate_refactoring_suggestions("Ecommerce API")
    check("Generated actionable architectural refactoring recommendations", len(refactor_recs) >= 2)

    section("7. AIForge Project Certification Engine")
    cert = global_certification_engine.certify_project("Ecommerce API")
    check("Issued AIForge Project Certification (Grade A+, Deployment Ready)", cert["overall_grade"] == "A+" and cert["deployment_ready"] == "YES")

    section("8. Persistent Quality Logs & Quality Dashboard")
    log_dir = Path(__file__).resolve().parents[1] / "logs"
    check("Persisted quality.log file", (log_dir / "quality.log").exists())
    check("Persisted security_scan.log file", (log_dir / "security_scan.log").exists())
    check("Persisted compliance.log file", (log_dir / "compliance.log").exists())
    check("Persisted metrics.log file", (log_dir / "metrics.log").exists())

    dashboard = global_certification_engine.get_quality_dashboard()
    check("Compiled Quality Dashboard metrics & trend data", dashboard["overall_quality_score"] >= 90 and len(dashboard["quality_trends"]) == 4)

    # Summary
    print("\n" + "="*70)
    print(f" AIFORGE V2 DAY 36 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = run_v2_day36_verification()
    sys.exit(0 if success else 1)
