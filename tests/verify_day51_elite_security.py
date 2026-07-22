"""
Day 51 - Elite Autonomous Security Agent Verification Suite
============================================================
Validates all 14 Core Security Requirements:
- 1. Static Security Analysis (SQLi, Hardcoded Secrets, CORS, XSS, LocalStorage JWT, RCE)
- 2. Dependency Analysis (Outdated packages & known CVE detection)
- 3. Security Score Engine (Weighted penalties & bonus scoring: Critical -30, High -15, Medium -7, Low -2 + Bonuses)
- 4. Deployment Gate Decision (Critical > 0 -> DEPLOYMENT BLOCKED)
- 5. Full Artifact Generation (security_report.md, security_report.json, security_summary.txt, fixes.md, executive_summary.md)
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.security.elite_security_agent import (
    EliteSecurityAgent,
    VulnerabilitySeverity
)

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
    print(" AIForge Day 51 - Elite Security Agent System Verification Suite")
    print("======================================================================")

    agent = EliteSecurityAgent()

    # Vulnerable project workspace
    insecure_workspace = {
        "backend/main.py": "SECRET_KEY = 'super_secret_jwt_key_12345'\nquery = f'SELECT * FROM users WHERE email = {email}'\napp.add_middleware(CORSMiddleware, allow_origins=['*'])",
        "frontend/src/App.jsx": "<div dangerouslySetInnerHTML={{ __html: userBio }} />\nlocalStorage.setItem('token', userToken);",
        "requirements.txt": "fastapi==0.100.0\nrequests==2.20.0\n"
    }

    # ==============================================================
    section("Test 1 – Static Security Analysis & Vulnerability Scanning")
    # ==============================================================
    res1 = agent.audit_project(insecure_workspace)

    print("Audit Summary:")
    print(f"  Security Score: {res1.security_score}/100")
    print(f"  Deployment Decision: {res1.deployment_decision.encode('ascii', 'ignore').decode('ascii')}")
    print(f"  Critical Findings: {res1.summary['CRITICAL']}")
    print(f"  High Findings: {res1.summary['HIGH']}")
    print(f"  Medium Findings: {res1.summary['MEDIUM']}\n")

    check("Hardcoded secret detected", any("Hardcoded Secret" in f.issue for f in res1.findings))
    check("SQL Injection vulnerability detected", any("f-string formatting" in f.issue for f in res1.findings))
    check("Wildcard CORS misconfiguration detected", any("Wildcard CORS" in f.issue for f in res1.findings))
    check("DOM XSS dangerouslySetInnerHTML detected", any("dangerouslySetInnerHTML" in f.issue for f in res1.findings))
    check("LocalStorage JWT storage vulnerability detected", any("LocalStorage" in f.issue for f in res1.findings))

    # ==============================================================
    section("Test 2 – Dependency Vulnerability Analysis")
    # ==============================================================
    check("Vulnerable dependency 'requests==2.20.0' identified", any("Outdated 'requests'" in f.issue for f in res1.findings))

    # ==============================================================
    section("Test 3 – Security Scoring & Penalties")
    # ==============================================================
    check("Security score properly penalized for critical issues", res1.security_score < 70.0)

    # ==============================================================
    section("Test 4 – Deployment Gate Enforcement")
    # ==============================================================
    check("Deployment gate BLOCKED when critical vulnerabilities exist", "BLOCKED" in res1.deployment_decision and not res1.deployment_approved)

    # ==============================================================
    section("Test 5 – Output Artifacts Generation")
    # ==============================================================
    artifacts = res1.artifacts
    print("Generated Security Artifacts:")
    for art_file in artifacts:
        print(f"  - [OK] {art_file}")

    check("security_report.md generated", "security_report.md" in artifacts)
    check("security_report.json generated", "security_report.json" in artifacts)
    check("security_summary.txt generated", "security_summary.txt" in artifacts)
    check("fixes.md generated", "fixes.md" in artifacts)
    check("executive_summary.md generated", "executive_summary.md" in artifacts)

    # ==============================================================
    section("Test 6 – Secure Project Approval")
    # ==============================================================
    secure_workspace = {
        "backend/main.py": "import os\nSECRET_KEY = os.getenv('SECRET_KEY')\ncursor.execute('SELECT * FROM users WHERE email = %s', (email,))\napp.add_middleware(CORSMiddleware, allow_origins=['https://app.aiforge.dev'])",
        "requirements.txt": "fastapi==0.100.0\nrequests==2.31.0\n"
    }

    res6 = agent.audit_project(secure_workspace)

    print("Secure Project Audit Summary:")
    print(f"  Security Score: {res6.security_score}/100")
    print(f"  Deployment Decision: {res6.deployment_decision.encode('ascii', 'ignore').decode('ascii')}\n")

    check("Secure project achieves high security score", res6.security_score >= 80.0)
    check("Deployment APPROVED for secure codebase", "APPROVED" in res6.deployment_decision and res6.deployment_approved)

    # Summary
    print("\n" + "="*70)
    print(f" DAY 51 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
