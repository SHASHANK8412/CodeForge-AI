"""
Stack detection and the Guardian's checks. Every check uses a fixed, controlled execution profile through
AIForge's existing isolated runners; nothing a project file says is executed as a command.

  python_syntax         static parse of every .py file (no code runs)                     Autopilot validation
  quality_gate          ruff / cross-file imports / oxlint blocking errors (static)         Autopilot validation
  security_static       Bandit (static); findings are warnings, never a pass/fail of the app Autopilot validation
  python_dependencies   pip install of requirements.txt in a throwaway container (network on, no capabilities)
  python_tests          pytest in a container with --network none, non-root, CPU/memory/process limits
  backend_startup       the FastAPI app in the hardened preview container until its readiness probe answers
  frontend_dependencies npm install in a throwaway container (no capabilities)
  frontend_build        npm run build in a container with --network none
  frontend_tests        npm run test in a container with --network none (only if the project defines it)
  api_contract          not run here (no contract is known); reported as SKIPPED with the reason

Without Docker the containerised checks are BLOCKED (never run on the host), except under the explicit
AIFORGE_TEST_SANDBOX=local opt-in used by AIForge's own test suite, where Python dependencies and tests run in
a per-project virtualenv and the environment says so. AIFORGE_GUARDIAN_CONTAINERS=off disables the container
checks (backend startup, frontend) - they are then BLOCKED, not passed.
"""

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from backend.evolution.autopilot.models import now_iso
from backend.evolution.autopilot.redact import redact
from backend.execution_guardian.models import Check

EXCERPT = 3000
CODE_SUFFIXES = (".py",)


def _excerpt(text: str, limit: int = EXCERPT) -> str:
    text = (text or "").strip()
    return redact(text[-limit:]) if text else ""


def containers_enabled() -> bool:
    return os.environ.get("AIFORGE_GUARDIAN_CONTAINERS", "on").strip().lower() not in ("off", "0", "false")


def _skip_dirs(rel_parts) -> bool:
    return bool({".venv", "venv", "node_modules", "__pycache__", ".git", "dist", "build"} & set(rel_parts))


def detect(project: Path) -> Dict[str, Any]:
    """What the project is, read from its files (nothing is executed)."""
    from backend.execution.preview_manager import backend_entry, frontend_entry
    from backend.execution.project_env import requirements_file
    py = [p for p in project.rglob("*.py") if not _skip_dirs(p.relative_to(project).parts)]
    tests = [p for p in py if p.name.startswith("test_") or p.name.endswith("_test.py")]
    entry = backend_entry(project)
    fe = frontend_entry(project)
    scripts: Dict[str, Any] = {}
    fe_dir = None
    if fe is not None:
        fe_dir = project if fe == "." else project / fe
        try:
            scripts = json.loads((fe_dir / "package.json").read_text(encoding="utf-8")).get("scripts") or {}
        except (OSError, ValueError):
            scripts = {}
    req = requirements_file(project)
    stack = {"python": bool(py), "python_files": len(py), "python_tests": len(tests),
             "requirements": req.relative_to(project).as_posix() if req else None,
             "fastapi_app": f"{entry['workdir']}/{entry['module']}" if entry else None,
             "frontend": fe, "frontend_scripts": sorted(scripts),
             "languages": sorted({x for x, on in (("python", bool(py)), ("javascript", fe is not None)) if on})}
    frameworks = []
    if entry:
        frameworks.append("FastAPI")
    if fe is not None:
        try:
            deps = json.loads((fe_dir / "package.json").read_text(encoding="utf-8"))
            names = {**(deps.get("dependencies") or {}), **(deps.get("devDependencies") or {})}
            frameworks += [n for n, k in (("React", "react"), ("Vite", "vite"), ("Vue", "vue")) if k in names]
        except (OSError, ValueError):
            pass
    stack["frameworks"] = frameworks
    return stack


def select(stack: Dict[str, Any]) -> List[Check]:
    """The checks that apply to this stack. Absent tests are SKIPPED (and keep the result below VERIFIED)."""
    out: List[Check] = []
    if stack["python"]:
        out += [Check(name="python_syntax", label="Python syntax", profile="static parse"),
                Check(name="quality_gate", label="Code-quality gate", profile="ruff, cross-file imports, oxlint (static)"),
                Check(name="security_static", label="Static security scan", required=False, profile="Bandit (static)"),
                Check(name="python_dependencies", label="Python dependency install",
                      profile="pip install -r requirements.txt in a throwaway container"),
                Check(name="python_tests", label="Python unit tests", profile="pytest in a no-network container")]
        if not stack["python_tests"]:
            out[-1].status, out[-1].reason = "SKIPPED", "the project has no Python test files"
    if stack["fastapi_app"]:
        out.append(Check(name="backend_startup", label="Backend startup", profile="hardened preview container + readiness probe"))
    if stack["frontend"] is not None:
        out += [Check(name="frontend_dependencies", label="Frontend dependency install", profile="npm install in a container"),
                Check(name="frontend_build", label="Frontend build", profile="npm run build in a no-network container")]
        if "test" in stack["frontend_scripts"]:
            out.append(Check(name="frontend_tests", label="Frontend tests", profile="npm run test in a no-network container"))
    out.append(Check(name="api_contract", label="API contract / integration", required=False, status="SKIPPED",
                     reason="frontend-to-backend calls are not tested here: the Integration & Compatibility Engine runs "
                            "the contract tests against the project's shared contract (and Swarm missions their own)"))
    return out


# --- running ------------------------------------------------------------------------------------------------------

def _start(c: Check) -> float:
    c.status, c.started_at = "RUNNING", now_iso()
    return time.perf_counter()


def _done(c: Check, t0: float, status: str, **kw) -> Check:
    c.status = status
    c.duration_seconds = round(time.perf_counter() - t0, 2)
    for k, v in kw.items():
        setattr(c, k, v)
    return c


def run_static(c: Check, project: Path) -> Check:
    from backend.evolution.autopilot import validation
    t0 = _start(c)
    fn = {"python_syntax": validation.check_python_syntax, "quality_gate": validation.check_quality_gate,
          "security_static": validation.check_security}[c.name]
    r = fn(project)
    status = {"passed": "PASSED", "failed": "FAILED", "blocked": "BLOCKED", "not_run": "SKIPPED", "error": "BLOCKED"}.get(r.status, "FAILED")
    return _done(c, t0, status, environment=r.environment, exit_code=r.exit_code, counts=r.counts,
                 log_excerpt=_excerpt(r.output) if status != "PASSED" else "", provenance="this verification",
                 error_summary="" if status == "PASSED" else (r.output or "").strip().splitlines()[0][:300] if r.output else status.lower())


def _pytest_counts(output: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    tail = output.strip().splitlines()[-1] if output.strip() else ""
    for n, kind in re.findall(r"(\d+) (passed|failed|errors?|skipped)", tail):
        counts["errors" if kind.startswith("error") else kind] = int(n)
    return counts


def run_python(deps: Optional[Check], tests: Optional[Check], project: Path, timeout: float) -> None:
    """Dependencies and tests in one isolated run (the install container, then the no-network test container)."""
    from backend.execution.docker_test_sandbox import docker_available, run_pytest_in_docker, sandbox_mode
    run_tests = tests is not None and tests.status != "SKIPPED"
    t0 = time.perf_counter()
    for c in (deps, tests if run_tests else None):
        if c is not None:
            _start(c)
    if sandbox_mode() == "local":
        _run_python_local(deps, tests if run_tests else None, project, t0)
        return
    if not docker_available():
        for c in (deps, tests if run_tests else None):
            if c is not None:
                _done(c, t0, "BLOCKED", reason="Docker is not available: generated code is only run in the Docker sandbox",
                      environment="unavailable")
        return
    env = "Docker sandbox (install: network on, no capabilities; tests: --network none, non-root, limits)"
    res = run_pytest_in_docker(project, timeout_seconds=timeout)
    status = getattr(res.status, "value", str(res.status))
    out = f"{res.stdout or ''}\n{res.stderr or ''}"
    if status == "INFRASTRUCTURE_ERROR" and res.exit_code == 3:
        if deps is not None:
            _done(deps, t0, "FAILED", environment=env, exit_code=3, log_excerpt=_excerpt(out), provenance="this verification",
                  error_summary="dependency install failed")
        if run_tests:
            _done(tests, t0, "BLOCKED", environment=env, reason="not run: the dependencies did not install")
        return
    if status == "INFRASTRUCTURE_ERROR":
        for c in (deps, tests if run_tests else None):
            if c is not None:
                _done(c, t0, "BLOCKED", environment=env, reason=_excerpt(out, 400) or "the sandbox could not run")
        return
    if deps is not None:
        _done(deps, t0, "PASSED", environment=env, provenance="this verification")
    if not run_tests:
        return
    if status == "TIMEOUT":
        _done(tests, t0, "FAILED", environment=env, timed_out=True, exit_code=res.exit_code, log_excerpt=_excerpt(out),
              error_summary=f"the tests did not finish within {timeout:.0f}s", provenance="this verification")
        return
    counts = _pytest_counts(res.stdout or "")
    if res.exit_code == 5:
        _done(tests, t0, "SKIPPED", environment=env, reason="pytest collected no tests", counts=counts)
        return
    _done(tests, t0, "PASSED" if res.exit_code == 0 else "FAILED", environment=env, exit_code=res.exit_code, counts=counts,
          log_excerpt="" if res.exit_code == 0 else _excerpt(out), provenance="this verification",
          error_summary="" if res.exit_code == 0 else f"{counts.get('failed', 0)} failed, {counts.get('errors', 0)} error(s)")


def _run_python_local(deps, tests, project: Path, t0: float) -> None:
    """AIFORGE_TEST_SANDBOX=local (AIForge's own test suite): a per-project virtualenv on this machine."""
    from backend.execution.project_env import ensure_project_env
    from backend.execution.project_runner import global_project_runner
    env = "local subprocess (AIFORGE_TEST_SANDBOX=local opt-in)"
    e = ensure_project_env(project)
    if deps is not None:
        _done(deps, t0, "PASSED" if e.get("ok") else "FAILED", environment=env, provenance="this verification",
              log_excerpt="" if e.get("ok") else _excerpt(e.get("log", "")), reason="no requirements.txt" if e.get("skipped") else "",
              error_summary="" if e.get("ok") else "dependency install failed")
    if tests is None:
        return
    if not e.get("ok"):
        _done(tests, t0, "BLOCKED", environment=env, reason="not run: the dependencies did not install")
        return
    res = global_project_runner.run_project(str(project))
    status = getattr(res.status, "value", str(res.status))
    out = f"{res.stdout or ''}\n{res.stderr or ''}"
    if status == "TIMEOUT":
        _done(tests, t0, "FAILED", environment=env, timed_out=True, log_excerpt=_excerpt(out), error_summary="the tests timed out",
              provenance="this verification")
        return
    if status in ("INFRASTRUCTURE_ERROR", "UNSUPPORTED"):
        _done(tests, t0, "BLOCKED", environment=env, reason=_excerpt(out, 400) or "the tests could not run")
        return
    counts = _pytest_counts(res.stdout or "")
    if res.exit_code == 5:
        _done(tests, t0, "SKIPPED", environment=env, reason="pytest collected no tests", counts=counts)
        return
    _done(tests, t0, "PASSED" if res.exit_code == 0 else "FAILED", environment=env, exit_code=res.exit_code, counts=counts,
          log_excerpt="" if res.exit_code == 0 else _excerpt(out), provenance="this verification",
          error_summary="" if res.exit_code == 0 else f"{counts.get('failed', 0)} failed, {counts.get('errors', 0)} error(s)")


def _container_gate(c: Check, t0: float) -> bool:
    from backend.execution.docker_test_sandbox import docker_available
    if not containers_enabled():
        _done(c, t0, "BLOCKED", environment="disabled", reason="container checks are disabled in this environment "
                                                              "(AIFORGE_GUARDIAN_CONTAINERS=off)")
        return False
    if not docker_available():
        _done(c, t0, "BLOCKED", environment="unavailable",
              reason="Docker is not available: the app is only started inside containers")
        return False
    return True


def run_backend_startup(c: Check, project: Path, stop: Callable[[], bool]) -> Check:
    from backend.performance.engineer import runner
    from backend.performance.engineer.models import Workload
    t0 = _start(c)
    if not _container_gate(c, t0):
        return c
    res, env = runner.measure({"app": project}, Workload(), stop, drive=lambda url, st: {"ready": True})
    m = res["app"]
    environment = f"hardened preview container ({env.image}); cleanup verified: {env.cleanup.get('verified')}"
    if m.status == "measured":
        return _done(c, t0, "PASSED", environment=environment, provenance="this verification",
                     error_summary="", reason=f"answered {m.readiness_probe} after {m.startup_seconds}s")
    if m.status == "unavailable" and "Docker" in (m.error or ""):
        return _done(c, t0, "BLOCKED", environment=environment, reason=m.error or "")
    if m.status == "cancelled":
        return _done(c, t0, "BLOCKED", environment=environment, reason="cancelled")
    return _done(c, t0, "FAILED", environment=environment, provenance="this verification",
                 error_summary=(m.error or "the app did not start")[:300], log_excerpt=_excerpt(m.logs_tail or m.error or ""))


def run_frontend(deps: Optional[Check], build: Optional[Check], ftests: Optional[Check], project: Path, fe: str,
                 timeout: float) -> None:
    from backend.execution.docker_test_sandbox import run_npm_in_docker
    t0 = time.perf_counter()
    for c in (deps, build, ftests):
        if c is not None:
            _start(c)
    if not _container_gate(build or deps, t0):
        gate = build or deps
        for c in (deps, build, ftests):
            if c is not None and c is not gate:
                _done(c, t0, "BLOCKED", environment=gate.environment, reason=gate.reason)
        return
    path = project if fe == "." else project / fe
    env = "Docker (npm install: no capabilities; scripts: --network none)"
    res = run_npm_in_docker(path, "build", timeout_seconds=timeout)
    status = getattr(res.status, "value", str(res.status))
    out = f"{res.stdout or ''}\n{res.stderr or ''}"
    if status == "INFRASTRUCTURE_ERROR" and res.exit_code == 3:
        _done(deps, t0, "FAILED", environment=env, exit_code=3, log_excerpt=_excerpt(out), error_summary="npm install failed",
              provenance="this verification")
        for c in (build, ftests):
            if c is not None:
                _done(c, t0, "BLOCKED", environment=env, reason="not run: the frontend dependencies did not install")
        return
    if status == "INFRASTRUCTURE_ERROR":
        for c in (deps, build, ftests):
            if c is not None:
                _done(c, t0, "BLOCKED", environment=env, reason=_excerpt(out, 400) or "the sandbox could not run")
        return
    _done(deps, t0, "PASSED", environment=env, provenance="this verification")
    if status == "TIMEOUT":
        _done(build, t0, "FAILED", environment=env, timed_out=True, error_summary=f"the build did not finish within {timeout:.0f}s",
              log_excerpt=_excerpt(out), provenance="this verification")
    else:
        _done(build, t0, "PASSED" if res.exit_code == 0 else "FAILED", environment=env, exit_code=res.exit_code,
              log_excerpt="" if res.exit_code == 0 else _excerpt(out), provenance="this verification",
              error_summary="" if res.exit_code == 0 else "npm run build failed")
    if ftests is not None:
        t1 = time.perf_counter()
        r2 = run_npm_in_docker(path, "test", timeout_seconds=timeout)
        out2 = f"{r2.stdout or ''}\n{r2.stderr or ''}"
        s2 = getattr(r2.status, "value", str(r2.status))
        if s2 == "INFRASTRUCTURE_ERROR":
            _done(ftests, t1, "BLOCKED", environment=env, reason=_excerpt(out2, 400) or "the sandbox could not run")
        else:
            _done(ftests, t1, "PASSED" if r2.exit_code == 0 else "FAILED", environment=env, exit_code=r2.exit_code,
                  timed_out=s2 == "TIMEOUT", log_excerpt="" if r2.exit_code == 0 else _excerpt(out2),
                  provenance="this verification", error_summary="" if r2.exit_code == 0 else "npm run test failed")


def run_all(checks: List[Check], project: Path, stack: Dict[str, Any], settings: Dict[str, Any],
            stop: Callable[[], bool], only: Optional[List[str]] = None,
            on_progress: Optional[Callable[[str], None]] = None) -> List[Check]:
    """Run the selected checks (or only the named ones), in a fixed order; static checks first."""
    timeout = float(settings.get("check_timeout_seconds", 600))
    by = {c.name: c for c in checks}

    def want(name):
        c = by.get(name)
        return c is not None and c.status != "SKIPPED" and (only is None or name in only)
    progress = on_progress or (lambda op: None)
    for name in ("python_syntax", "quality_gate", "security_static"):
        if want(name) and not stop():
            progress(f"running {by[name].label}")
            run_static(by[name], project)
    if (want("python_dependencies") or want("python_tests")) and not stop():
        progress("installing Python dependencies and running the tests (isolated)")
        run_python(by.get("python_dependencies") if want("python_dependencies") else None,
                   by.get("python_tests") if want("python_tests") else None, project, timeout)
    if want("backend_startup") and not stop():
        progress("starting the backend in a hardened container")
        run_backend_startup(by["backend_startup"], project, stop)
    if any(want(n) for n in ("frontend_dependencies", "frontend_build", "frontend_tests")) and not stop():
        progress("installing frontend dependencies and building (isolated)")
        run_frontend(by.get("frontend_dependencies"), by.get("frontend_build"), by.get("frontend_tests") if want("frontend_tests") else None,
                     project, stack["frontend"], timeout)
    for c in checks:
        if c.status in ("PENDING", "RUNNING") and (only is None or c.name in only):
            c.status, c.reason = "BLOCKED", c.reason or "not run: the verification was stopped"
    return checks


def final_status(checks: List[Check]) -> Tuple[str, List[str]]:
    """VERIFIED only when every required check actually passed. Returns (status, warnings)."""
    required = [c for c in checks if c.required]
    warnings = []
    if any(c.status == "FAILED" for c in required):
        return "FAILED", warnings
    if any(c.status in ("BLOCKED", "PENDING", "RUNNING") for c in required):
        return "BLOCKED", warnings
    warnings += [f"{c.label} was not run: {c.reason}" for c in required if c.status == "SKIPPED"]
    warnings += [f"{c.label}: {c.status.lower()}" + (f" ({c.error_summary})" if c.error_summary else "")
                 for c in checks if not c.required and c.status in ("FAILED", "BLOCKED")]
    if not any(c.status == "PASSED" for c in required):
        return "BLOCKED", warnings + ["no required check ran"]
    return ("VERIFIED_WITH_WARNINGS" if warnings else "VERIFIED"), warnings
