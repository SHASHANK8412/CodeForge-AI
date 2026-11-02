"""
Regression tests: reports are built from real results, never from hardcoded success claims.
"""
from backend.security.security_agent import SecurityAgent
from backend.services.generation_service import project_generation_summary


def test_project_summary_reports_failed_checks_and_unrun_checks():
    summary = project_generation_summary({
        "project_name": "Todo",
        "quality_score": 72.5,
        "files": {"backend/main.py": "", "frontend/package.json": "{}"},
        "quality_gates": {"gate_checks": [
            {"id": 1, "name": "Folder Structure Integrity", "passed": True},
            {"id": 2, "name": "Routing Contracts Integrity", "passed": False},
        ]},
    }, "build a todo app")

    assert "72.5 / 100" in summary
    assert "1 / 2 passed (failed: Routing Contracts Integrity)" in summary
    assert "**Security scan**: not run" in summary
    assert "**Requirement match**: not run" in summary
    for fabricated in ("15 / 15", "CLEAN", "Zero Vulnerabilities", "45ms"):
        assert fabricated not in summary
    assert "cd backend && uvicorn main:app --reload" in summary and "npm run dev" in summary


def test_project_summary_without_frontend_has_no_frontend_instructions():
    summary = project_generation_summary({"files": {"main.py": ""}}, "api")
    assert "npm" not in summary and "uvicorn main:app --reload" in summary
    assert "**Quality score**: not computed" in summary


def test_security_agent_does_not_floor_its_score():
    files = {f"web/page{i}.js": "const key = 'supersecret';\n" for i in range(3)}
    _, report = SecurityAgent().scan_and_remedy(files)
    assert report["vulnerabilities_found"] == 3 and report["vulnerabilities_auto_fixed"] == 0
    assert report["security_score"] == 70.0
    assert report["status"] == "NEEDS_REVIEW"


def test_security_agent_secret_fix_has_no_fallback_secret():
    src = '"""Settings."""\nfrom __future__ import annotations\n\nSECRET_KEY = "supersecret"\n'
    fixed, report = SecurityAgent().scan_and_remedy({"backend/config.py": src})
    out = fixed["backend/config.py"]
    assert 'SECRET_KEY = os.environ["SECRET_KEY"]' in out
    assert "supersecret" not in out and "getenv" not in out
    assert out.splitlines()[:3] == ['"""Settings."""', "from __future__ import annotations", "import os"]
    compile(out, "config.py", "exec")
    assert report["findings"][0]["status"] == "AUTO_FIXED"
