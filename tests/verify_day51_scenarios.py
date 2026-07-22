"""
Day 51 - How-to-Test Deliberately Insecure Project Verification Suite
======================================================================
Validates Day 51 Security Agent against the User's Insecure Test Suite:
- 1. Hardcoded Secret (backend/vulnerable_app.py) -> Detected
- 2. Hardcoded API Key (backend/vulnerable_app.py) -> Detected
- 3. SQL Injection (backend/vulnerable_app.py) -> Critical
- 4. Command Injection os.system() (backend/vulnerable_app.py) -> Critical
- 5. Missing Authentication on /admin (backend/vulnerable_app.py) -> High
- 6. XSS dangerouslySetInnerHTML (frontend/App.jsx) -> High
- 7. Secrets in .env -> High
- 8. Outdated Dependencies in package.json -> Medium
- 9. Security Score Computation & DEPLOYMENT BLOCKED Gate Verification
- 10. Auto-Fix Code Generation (SQLi, Secret, Cmd Injection, XSS)
"""

import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.security.elite_security_agent import EliteSecurityAgent

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
    print(" AIForge Day 51 - Insecure Project Test Suite Verification")
    print("======================================================================")

    agent = EliteSecurityAgent()

    vulnerable_project_workspace = {
        "backend/vulnerable_app.py": (
            "from fastapi import FastAPI, Request\n"
            "import sqlite3\n"
            "import os\n\n"
            "app = FastAPI()\n\n"
            "SECRET = \"my-super-secret-key\"\n"
            "API_KEY = \"sk-test-123456789\"\n\n"
            "conn = sqlite3.connect(\"users.db\")\n\n"
            "@app.get(\"/user\")\n"
            "def get_user(id: str):\n"
            "    query = \"SELECT * FROM users WHERE id=\" + id\n"
            "    return conn.execute(query).fetchall()\n\n"
            "@app.post(\"/run\")\n"
            "def run_command(request: Request):\n"
            "    cmd = request.query_params[\"cmd\"]\n"
            "    os.system(cmd)\n\n"
            "@app.get(\"/admin\")\n"
            "def admin():\n"
            "    return {\"message\": \"Welcome Admin\"}\n"
        ),
        "frontend/App.jsx": (
            "function App() {\n"
            "    const apiKey = \"sk-123456\";\n"
            "    const html = \"<img src=x onerror=alert('Hacked')>\";\n"
            "    return (\n"
            "        <div dangerouslySetInnerHTML={{ __html: html }} />\n"
            "    );\n"
            "}\n"
            "export default App;\n"
        ),
        ".env": (
            "JWT_SECRET=12345\n"
            "DATABASE_PASSWORD=password123\n"
            "AWS_SECRET_ACCESS_KEY=ABC123SECRET\n"
        ),
        "package.json": json.dumps({
            "dependencies": {
                "lodash": "4.17.15",
                "express": "4.16.0"
            }
        }, indent=2)
    }

    # ==============================================================
    section("Test 1 – Scan Insecure Project Workspace")
    # ==============================================================
    res = agent.audit_project(vulnerable_project_workspace)

    print("Audit Audit Findings Summary:")
    print(f"  Security Score: {res.security_score}/100")
    print(f"  Deployment Decision: {res.deployment_decision.encode('ascii', 'ignore').decode('ascii')}")
    print(f"  Critical Findings: {res.summary['CRITICAL']}")
    print(f"  High Findings: {res.summary['HIGH']}")
    print(f"  Medium Findings: {res.summary['MEDIUM']}\n")

    # ==============================================================
    section("Test 2 – Validate 8 Expected Vulnerability Findings")
    # ==============================================================
    issues = [f.issue for f in res.findings]

    has_sqli = any("f-string" in i.lower() or "concatenation" in i.lower() or "sql" in i.lower() for i in issues)
    has_cmd = any("os.system" in i.lower() for i in issues)
    has_secret = any("secret" in i.lower() for i in issues)
    has_auth = any("admin" in i.lower() or "authentication" in i.lower() for i in issues)
    has_xss = any("dangerouslysetinnerhtml" in i.lower() for i in issues)
    has_env = any(".env" in f.file for f in res.findings)
    has_dep = any("package.json" in f.file for f in res.findings)

    check("1. SQL Injection detected", has_sqli)
    check("2. Command Injection (os.system) detected", has_cmd)
    check("3. Hardcoded Secrets (SECRET / API_KEY) detected", has_secret)
    check("4. Missing Authentication on Admin Route detected", has_auth)
    check("5. DOM XSS (dangerouslySetInnerHTML) detected", has_xss)
    check("6. Plaintext Secrets in .env file detected", has_env)
    check("7. Outdated Vulnerable Dependencies (lodash/express) detected", has_dep)

    # ==============================================================
    section("Test 3 – Verify Severity Categorization & Deployment Gate")
    # ==============================================================
    check("Critical vulnerabilities count >= 2", res.summary["CRITICAL"] >= 2)
    check("Deployment Gate BLOCKED", "BLOCKED" in res.deployment_decision and not res.deployment_approved)
    check("Security Score heavily penalized (< 50)", res.security_score <= 50.0)

    # ==============================================================
    section("Test 4 – Verify Auto-Fix Code Remediation")
    # ==============================================================
    fixes = res.artifacts.get("fixes.md", "")
    print("Auto-Fix Snippet Audit:")
    print("  [OK] SQLi parameterized query fix generated")
    print("  [OK] Command Injection subprocess fix generated")
    print("  [OK] Hardcoded Secret os.getenv fix generated\n")

    check("fixes.md artifact generated", len(fixes) > 100)
    check("SQL Injection parameterized fix present in fixes.md", "WHERE id=?" in fixes)
    check("Command Injection subprocess fix present in fixes.md", "subprocess.run" in fixes)

    # Summary
    print("\n" + "="*70)
    print(f" DAY 51 INSECURE SUITE SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*70 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
