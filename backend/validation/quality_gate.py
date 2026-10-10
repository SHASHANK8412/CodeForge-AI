"""
Code-quality gate for generated projects.

Blocking errors are real defects, not style: Python syntax errors, undefined names and invalid
comparisons (ruff E9, F63, F7, F82), and JS/JSX parse and correctness errors (oxlint). Unused
imports and variables are reported as warnings. The pipeline treats blocking errors like failing
tests, so they go through the debug -> patch -> retest loop.
"""

import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_logger = logging.getLogger("aiforge.validation.quality_gate")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_EXCLUDE = [".venv", "node_modules", "dist", "build", "__pycache__", ".aiforge_checkpoints"]
_PY_BLOCKING = "E9,F63,F7,F82"
_JS_WARNING_RULES = {"no-unused-vars"}


def _oxlint() -> Optional[str]:
    """oxlint ships with AIForge's frontend dev dependencies; absent in the backend-only image."""
    bin_dir = _REPO_ROOT / "frontend" / "node_modules" / ".bin"
    for name in ("oxlint.cmd", "oxlint") if sys.platform == "win32" else ("oxlint",):
        if (bin_dir / name).is_file():
            return str(bin_dir / name)
    return shutil.which("oxlint")


def _python_issues(project: Path) -> Optional[List[Dict[str, Any]]]:
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(project), "--select", _PY_BLOCKING,
             "--output-format", "json", "--no-cache", "--exclude", ",".join(_EXCLUDE)],
            capture_output=True, text=True, timeout=120,
        )
        findings = json.loads(proc.stdout or "[]")
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as e:
        _logger.warning("Quality gate: ruff unavailable (%s)", e)
        return None
    return [{
        "tool": "ruff", "severity": "error", "code": f.get("code") or "syntax",
        "file": Path(f["filename"]).resolve().relative_to(project).as_posix(),
        "line": (f.get("location") or {}).get("row"), "message": f.get("message", ""),
    } for f in findings]


def _js_issues(project: Path) -> Optional[List[Dict[str, Any]]]:
    exe = _oxlint()
    if not exe:
        return None
    sources = [p for p in project.rglob("*") if p.suffix in (".js", ".jsx", ".ts", ".tsx")
               and not set(_EXCLUDE) & set(p.relative_to(project).parts)]
    if not sources:
        return []
    try:
        proc = subprocess.run(
            [exe, "--format", "json", "-A", "all", "-D", "correctness",
             *[f"--ignore-pattern=**/{d}/**" for d in _EXCLUDE], str(project)],
            capture_output=True, text=True, timeout=120, shell=False,
        )
        diagnostics = json.loads(proc.stdout or "{}").get("diagnostics", [])
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as e:
        _logger.warning("Quality gate: oxlint failed (%s)", e)
        return None
    issues = []
    for d in diagnostics:
        code = d.get("code") or "parse-error"
        rule = code.split("(")[-1].rstrip(")")
        span = ((d.get("labels") or [{}])[0].get("span") or {})
        try:
            rel = Path(d.get("filename", "")).resolve().relative_to(project).as_posix()
        except ValueError:
            rel = d.get("filename", "")
        issues.append({
            "tool": "oxlint", "severity": "warning" if rule in _JS_WARNING_RULES else "error",
            "code": code, "file": rel, "line": span.get("line"), "message": d.get("message", ""),
        })
    return issues


def run_quality_gate(project_dir: Any) -> Dict[str, Any]:
    project = Path(project_dir).resolve()
    if not project.is_dir():
        return {"passed": False, "errors": [], "warnings": [], "skipped": ["project folder not found"]}

    py = _python_issues(project)
    js = _js_issues(project)
    issues = (py or []) + (js or [])
    skipped = [name for name, res in (("python (ruff unavailable)", py), ("javascript (oxlint unavailable)", js)) if res is None]
    errors = [i for i in issues if i["severity"] == "error"]
    return {
        "passed": not errors,
        "errors": errors[:100],
        "warnings": [i for i in issues if i["severity"] == "warning"][:100],
        "error_count": len(errors),
        "warning_count": len(issues) - len(errors),
        "skipped": skipped,
    }


def format_issues(issues: List[Dict[str, Any]], limit: int = 20) -> List[str]:
    return [f"{i['file']}:{i.get('line') or '?'}: [{i['code']}] {i['message']}" for i in issues[:limit]]


# --- Release report: deterministic checks only, never model-reported results -----------------

def _bandit_findings(project: Path) -> Optional[List[Dict[str, Any]]]:
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "bandit", "-r", str(project), "-f", "json", "-q",
             "-x", ",".join(f"*/{d}/*" for d in (*_EXCLUDE, "tests"))],
            capture_output=True, text=True, timeout=180,
        )
        results = json.loads(proc.stdout or "{}").get("results", [])
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as e:
        _logger.warning("Quality report: bandit unavailable (%s)", e)
        return None
    return [{
        "tool": "bandit", "code": r.get("test_id"), "severity": r.get("issue_severity", "LOW").upper(),
        "confidence": r.get("issue_confidence", "LOW").upper(),
        "file": Path(r["filename"]).resolve().relative_to(project).as_posix(),
        "line": r.get("line_number"), "message": r.get("issue_text", ""),
    } for r in results]


def _dependency_findings(project: Path) -> Optional[List[Dict[str, Any]]]:
    """Known-vulnerable pinned requirements via pip-audit (needs network; skipped if unavailable)."""
    from backend.execution.project_env import requirements_file
    req = requirements_file(project)
    if req is None:
        return []
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pip_audit", "-r", str(req), "--format", "json", "--progress-spinner", "off"],
            capture_output=True, text=True, timeout=300,
        )
        data = json.loads(proc.stdout or "{}")
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as e:
        _logger.info("Quality report: dependency audit skipped (%s)", e)
        return None
    deps = data.get("dependencies", []) if isinstance(data, dict) else data
    return [{
        "tool": "pip-audit", "code": v.get("id"), "severity": "HIGH", "file": req.relative_to(project).as_posix(),
        "line": None, "message": f"{d.get('name')} {d.get('version')}: {v.get('id')} (fixed in {', '.join(v.get('fix_versions') or []) or 'no release yet'})",
    } for d in deps for v in (d.get("vulns") or [])]


def run_quality_report(project_dir: Any, gate: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Machine-readable quality report built from executed tools: the code-quality gate, Bandit
    (Python security) and pip-audit (vulnerable dependencies). Recommendation:
    "blocked" when the gate fails or there is a HIGH-severity, HIGH-confidence security finding
    or a vulnerable dependency; "review_required" for remaining MEDIUM/HIGH findings; else "ready".
    """
    project = Path(project_dir).resolve()
    gate = gate or run_quality_gate(project)
    bandit = _bandit_findings(project)
    deps = _dependency_findings(project)

    security = (bandit or []) + (deps or [])
    critical = [f for f in security if f["tool"] == "pip-audit" or (f["severity"] == "HIGH" and f.get("confidence") == "HIGH")]
    review = [f for f in security if f not in critical and f["severity"] in ("HIGH", "MEDIUM")]
    checks = {
        "code_quality_gate": "passed" if gate.get("passed") else "failed",
        "python_security": "skipped" if bandit is None else ("failed" if any(f["tool"] == "bandit" for f in critical) else "passed"),
        "dependency_audit": "skipped" if deps is None else ("failed" if deps else "passed"),
    }
    if not gate.get("passed") or critical:
        recommendation = "blocked"
    elif review:
        recommendation = "review_required"
    else:
        recommendation = "ready"
    return {
        "checks": checks,
        "checks_passed": sum(1 for v in checks.values() if v == "passed"),
        "checks_failed": sum(1 for v in checks.values() if v == "failed"),
        "checks_skipped": [k for k, v in checks.items() if v == "skipped"],
        "critical_findings": len(critical),
        "review_findings": len(review),
        "findings": (critical + review)[:50],
        "release_recommendation": recommendation,
    }
