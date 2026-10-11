"""
Validation checks and the baseline-vs-after comparison that decides whether a change is accepted.

Every check records what ran, where, when, its exit status and (redacted) output. Counts are only
reported when the tool's own summary states them. A check that could not run is "blocked" or
"not_run", never "passed".
"""

import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.evolution.autopilot.codebase import iter_project_files, read_text
from backend.evolution.autopilot.models import CheckResult, now_iso
from backend.evolution.autopilot.redact import redact

OUTPUT_LIMIT = 6000


def _result(check_id, label, environment, started, status, exit_code=None, counts=None, output="") -> CheckResult:
    return CheckResult(check_id=check_id, label=label, environment=environment, started_at=started,
                       finished_at=now_iso(), status=status, exit_code=exit_code, counts=counts or {},
                       output=redact(output, OUTPUT_LIMIT))


def check_python_syntax(project: Path) -> CheckResult:
    started = now_iso()
    errors, files = [], 0
    for rel, path, size in iter_project_files(project):
        if not rel.endswith(".py"):
            continue
        source = read_text(path, size)
        if source is None:
            continue
        files += 1
        try:
            ast.parse(source)
        except SyntaxError as e:
            errors.append(f"{rel}:{e.lineno}: {e.msg}")
    if not files:
        return _result("python_syntax", "Python syntax", "static parse (no code executed)", started, "not_run",
                       output="no Python files")
    return _result("python_syntax", "Python syntax", "static parse (no code executed)", started,
                   "failed" if errors else "passed", 1 if errors else 0,
                   {"files": files, "errors": len(errors)}, "\n".join(errors))


def check_quality_gate(project: Path) -> CheckResult:
    from backend.validation.quality_gate import format_issues, run_quality_gate
    started = now_iso()
    gate = run_quality_gate(project)
    skipped = gate.get("skipped") or []
    output = "\n".join(format_issues(gate.get("errors", []), limit=50))
    if skipped:
        output += "\nnot checked: " + ", ".join(skipped)
    status = "passed" if gate.get("passed") else "failed"
    if not gate.get("errors") and skipped and len(skipped) >= 2:
        status = "blocked"
    return _result("quality_gate", "Code-quality gate (ruff, cross-file imports, oxlint)",
                   "static analysis (no code executed)", started, status, 0 if status == "passed" else 1,
                   {"errors": gate.get("error_count", 0), "warnings": gate.get("warning_count", 0)}, output)


def check_security(project: Path) -> CheckResult:
    from backend.validation.quality_gate import _bandit_findings
    started = now_iso()
    findings = _bandit_findings(project)
    if findings is None:
        return _result("security_static", "Static security scan (Bandit)", "static analysis", started, "blocked",
                       output="Bandit is not available")
    high = [f for f in findings if f.get("severity") == "HIGH"]
    lines = [f"{f.get('file')}:{f.get('line')}: [{f.get('code')}] {f.get('severity')} {f.get('message')}" for f in findings]
    return _result("security_static", "Static security scan (Bandit)", "static analysis", started,
                   "failed" if high else "passed", 1 if high else 0,
                   {"findings": len(findings), "high": len(high)}, "\n".join(lines[:60]))


def _test_counts(output: str, language: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    if language == "python":
        tail = output[-3000:]
        for key in ("passed", "failed", "error", "errors", "skipped"):
            m = re.findall(rf"(\d+) {key}\b", tail)
            if m:
                counts["errors" if key == "error" else key] = int(m[-1])
    else:
        for key, pattern in (("passed", r"#\s*pass\s+(\d+)"), ("failed", r"#\s*fail\s+(\d+)"),
                             ("passed", r"Tests:.*?(\d+) passed"), ("failed", r"Tests:.*?(\d+) failed"),
                             ("passed", r"(\d+)\s+passing"), ("failed", r"(\d+)\s+failing")):
            m = re.search(pattern, output)
            if m and key not in counts:
                counts[key] = int(m.group(1))
    return counts


def check_tests(project: Path, disposable: bool = False) -> CheckResult:
    """
    The project's tests, under AIForge's sandbox policy (Docker; never the host by default).
    The test runner prepares the folder it runs in (package markers, a project venv), so unless
    `project` is already a disposable working copy, the tests run in a fresh copy of it.
    """
    from backend.evolution.autopilot.workspace import create_workspace, discard_workspace
    if not disposable:
        copy = create_workspace(project, prefix="aiforge_autopilot_check_")
        try:
            return check_tests(copy, disposable=True)
        finally:
            discard_workspace(copy)
    from backend.execution.docker_test_sandbox import sandbox_mode, should_use_docker
    from backend.execution.project_runner import global_project_runner
    started = now_iso()
    cmd, language = global_project_runner.select_safe_command(project)
    if not cmd or "compileall" in cmd:
        return _result("tests", "Project tests", "-", started, "not_run", output="no tests found in the project")
    environment = ("Docker sandbox (no network, non-root)" if should_use_docker() and sandbox_mode() != "local"
                   else "local subprocess (AIFORGE_TEST_SANDBOX=local)" if sandbox_mode() == "local" else "unavailable")
    res = global_project_runner.run_project(str(project))
    output = f"{res.stdout or ''}\n{res.stderr or ''}"
    status_name = getattr(res.status, "value", str(res.status))
    if status_name in ("INFRASTRUCTURE_ERROR", "UNSUPPORTED") and res.exit_code in (-1, 3):
        return _result("tests", "Project tests", environment, started, "blocked", res.exit_code, output=output)
    if status_name == "TIMEOUT":
        return _result("tests", "Project tests", environment, started, "error", res.exit_code, output=output)
    counts = _test_counts(output, language)
    status = "passed" if res.exit_code == 0 else "failed"
    return _result("tests", "Project tests", environment, started, status, res.exit_code, counts, output)


def run_checks(project: Any, include_tests: bool = True, disposable: bool = False) -> List[CheckResult]:
    project = Path(project).resolve()
    checks = [check_python_syntax(project), check_quality_gate(project), check_security(project)]
    if include_tests:
        checks.append(check_tests(project, disposable=disposable))
    return checks


def _by_id(checks: List[CheckResult]) -> Dict[str, CheckResult]:
    return {c.check_id: c for c in checks}


def compare(baseline: List[CheckResult], after: List[CheckResult]) -> Dict[str, Any]:
    """
    Acceptance rules (a change is accepted only if none is broken):
      * syntax: no new Python syntax errors
      * quality gate: blocking errors do not increase
      * security: high-severity static findings do not increase
      * tests: a passing suite stays passing; for a suite that already failed, passed tests do
        not decrease and failed/errored tests do not increase
    A check that could not run after the change (but ran before) makes the result unverified.
    """
    before, now = _by_id(baseline), _by_id(after)
    regressions, unverified, notes = [], [], []

    def counts(c: Optional[CheckResult], key: str) -> int:
        return (c.counts.get(key, 0) if c else 0)

    for check_id in ("python_syntax", "quality_gate", "security_static", "tests"):
        b, a = before.get(check_id), now.get(check_id)
        if a is None:
            continue
        if a.status in ("blocked", "error", "not_run"):
            if b is not None and b.status in ("passed", "failed"):
                unverified.append(f"{a.label} could not run after the change ({a.status})")
            else:
                notes.append(f"{a.label}: {a.status} before and after - not used as evidence")
            continue
        if check_id == "python_syntax" and counts(a, "errors") > counts(b, "errors"):
            regressions.append(f"syntax errors {counts(b, 'errors')} -> {counts(a, 'errors')}")
        if check_id == "quality_gate" and counts(a, "errors") > counts(b, "errors"):
            regressions.append(f"quality-gate errors {counts(b, 'errors')} -> {counts(a, 'errors')}")
        if check_id == "security_static" and counts(a, "high") > counts(b, "high"):
            regressions.append(f"high-severity security findings {counts(b, 'high')} -> {counts(a, 'high')}")
        if check_id == "tests" and b is not None and b.status in ("passed", "failed"):
            if b.status == "passed" and a.status == "failed":
                regressions.append("tests passed before the change and fail after it")
            elif b.status == "failed" and a.status == "failed":
                if counts(a, "passed") < counts(b, "passed"):
                    regressions.append(f"passing tests {counts(b, 'passed')} -> {counts(a, 'passed')}")
                bad_b = counts(b, "failed") + counts(b, "errors")
                bad_a = counts(a, "failed") + counts(a, "errors")
                if bad_a > bad_b:
                    regressions.append(f"failing tests {bad_b} -> {bad_a}")
                if not b.counts and not a.counts:
                    unverified.append("tests failed before and after; without counts no comparison is possible")
            elif b.status == "failed" and a.status == "passed":
                notes.append("tests that failed before the change pass after it")
        elif check_id == "tests" and b is not None and b.status in ("blocked", "error", "not_run") and a.status == "passed":
            notes.append("tests could not run before the change; they pass after it")

    executed = [c.check_id for c in after if c.status in ("passed", "failed")]
    return {
        "accepted": not regressions and not unverified,
        "regressions": regressions,
        "unverified": unverified,
        "notes": notes,
        "evidence": "tests and static checks" if "tests" in executed else
                    ("static checks only - tests did not run" if executed else "no checks ran"),
    }
