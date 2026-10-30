"""
Recorded evidence about a generated project, and the quality gates computed from it.

Sources (nothing is estimated, nothing is assumed to have passed):
  the Execution Guardian's latest verification   checks that ran on the project: syntax, quality gate, static
                                                 security scan, dependency install, tests, backend startup, frontend
  the Integration Engine's latest run            frontend / backend / database compatibility with the contract
  the project's files                            documentation present

A gate no recorded check covers is NOT_EVALUATED, with the reason; it is never counted as passed and has no score.
The Quality Center and the CTO readiness gate both read from here.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

GATE_OK = ("PASSED",)
GATE_EVALUATED = ("PASSED", "FAILED", "WARNING", "BLOCKED", "SKIPPED")
GUARDIAN_GATES = (
    ("python_syntax", "Python Syntax"),
    ("quality_gate", "Code-Quality Gate"),
    ("security_static", "Static Security Scan"),
    ("python_dependencies", "Python Dependency Install"),
    ("python_tests", "Python Tests"),
    ("backend_startup", "Backend Startup"),
    ("frontend_dependencies", "Frontend Dependency Install"),
    ("frontend_build", "Frontend Build"),
    ("frontend_tests", "Frontend Tests"),
)
OPEN = ("open", "unresolved", "needs_contract_decision", "blocked")


def _keys(generation_id: str, project_dir: Optional[Path]) -> List[str]:
    """The ids a project's records may be kept under: the generation id (API runs) and the project name the
    generation workflow used."""
    keys = [generation_id]
    try:
        from backend.generation.store import global_generation_store
        rec = global_generation_store.get(generation_id) or {}
        keys += [str(rec.get(k)) for k in ("project_id", "project_name") if rec.get(k)]
    except Exception:  # noqa: BLE001 - the generation id alone still identifies API runs
        pass
    if project_dir is not None:
        keys.append(Path(project_dir).name)
    return list(dict.fromkeys(k for k in keys if k))


def latest_verification(keys: List[str]):
    from backend.execution_guardian.service import global_execution_guardian
    found = []
    for k in keys:
        try:
            found += [v for v in global_execution_guardian.store.list(k, "verifications") if v.status != "RUNNING"]
        except ValueError:                       # a key that is not a valid store id
            continue
    return max(found, key=lambda v: v.started_at) if found else None


def latest_integration(keys: List[str]):
    from backend.compatibility.service import global_integration_engine
    found = []
    for k in keys:
        try:
            found += [r for r in global_integration_engine.runs(k) if r.finished_at]
        except ValueError:
            continue
    return max(found, key=lambda r: r.started_at) if found else None


def collect(generation_id: str, project_dir: Optional[Path]) -> Dict[str, Any]:
    keys = _keys(generation_id, project_dir)
    return {"keys": keys, "verification": latest_verification(keys), "integration": latest_integration(keys),
            "project_dir": Path(project_dir) if project_dir else None}


def _gate(gid: int, name: str, status: str, findings: List[str], recommendation: str, source: str,
          counts: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
    c = counts or {}
    return {"id": gid, "name": f"{gid:02d} {name}", "status": status, "score": None, "critical": c.get("critical", 0),
            "high": c.get("high", 0), "medium": c.get("medium", 0), "low": c.get("low", 0), "findings": findings,
            "recommendation": recommendation, "source": source}


def gates(ev: Dict[str, Any]) -> List[Dict[str, Any]]:
    v, r, root = ev["verification"], ev["integration"], ev["project_dir"]
    out: List[Dict[str, Any]] = []
    gid = 1
    out.append(_gate(gid, "Requirements Fidelity", "NOT_EVALUATED",
                     ["AIForge has no check yet that the code implements the request"],
                     "Review the generated features against the request yourself", "not evaluated"))
    # API and database compatibility (Integration Engine)
    if r is None:
        for name in ("API Contract Compatibility", "Database Compatibility"):
            gid += 1
            out.append(_gate(gid, name, "NOT_EVALUATED", ["no Integration Engine run is recorded for this project"],
                             "Run Integration Engine → Verify", "not evaluated"))
    else:
        open_ = [f for f in r.findings if f.status in OPEN]
        api = [f for f in open_ if not f.rule.startswith("db_")]
        db = [f for f in open_ if f.rule.startswith("db_")]
        status_api = {"COMPATIBLE": "PASSED", "COMPATIBLE_WITH_WARNINGS": "WARNING", "INCOMPATIBLE": "FAILED",
                      "BLOCKED": "BLOCKED", "CANCELLED": "NOT_EVALUATED"}.get(r.status, "NOT_EVALUATED")
        gid += 1
        out.append(_gate(gid, "API Contract Compatibility", status_api,
                         [f"{f.severity}: {f.rule} {f.target}" for f in api[:6]] or [(r.report or {}).get("statement", r.status)],
                         "Fix the open findings (Integration Engine)" if api else "None", f"integration run {r.id}",
                         _sev(api)))
        db_cov = [c for c in r.coverage if c["check"].startswith("database entities")]
        db_status = ("FAILED" if any(f.severity in ("critical", "high") for f in db) else "WARNING" if db
                     else "PASSED" if any(c["status"] == "checked" for c in db_cov) else "NOT_EVALUATED")
        gid += 1
        out.append(_gate(gid, "Database Compatibility", db_status,
                         [f"{f.severity}: {f.rule} {f.target}" for f in db[:6]] or [c["detail"] for c in db_cov[:2]]
                         or ["the contract or the project has no database to compare"],
                         "Fix the open database findings" if db else "None", f"integration run {r.id}", _sev(db)))
    # Checks the Execution Guardian ran
    by = {c.name: c for c in (v.checks if v else [])}
    for name, label in GUARDIAN_GATES:
        gid += 1
        c = by.get(name)
        if v is None:
            out.append(_gate(gid, label, "NOT_EVALUATED", ["no Execution Guardian verification is recorded for this project"],
                             "Run Execution Guardian → Verify", "not evaluated"))
            continue
        if c is None:
            out.append(_gate(gid, label, "NOT_EVALUATED", ["does not apply to this project's stack"], "None",
                             f"verification {v.id}"))
            continue
        status = {"PASSED": "PASSED", "FAILED": "FAILED", "BLOCKED": "BLOCKED", "SKIPPED": "SKIPPED"}.get(c.status, "NOT_EVALUATED")
        if name == "security_static" and status == "FAILED":
            status = "WARNING"                   # Bandit findings are warnings, never a pass/fail of the app
        detail = c.error_summary or c.reason or ("passed" if status == "PASSED" else c.status.lower())
        if c.counts:
            detail += " (" + ", ".join(f"{n} {k}" for k, n in c.counts.items()) + ")"
        fails = [f for f in v.failures if f.check == name]
        out.append(_gate(gid, label, status, [detail] + [f"{f.category}: {f.summary}" for f in fails[:3]],
                         (fails[0].next_action if fails else "None") or "None", f"verification {v.id}",
                         _sev(fails)))
    gid += 1
    readme = next((p for p in ((root / n) for n in ("README.md", "readme.md", "README")) if p.is_file()), None) if root else None
    if root is None:
        out.append(_gate(gid, "Documentation", "NOT_EVALUATED", ["the project folder was not found"], "None", "not evaluated"))
    elif readme is None:
        out.append(_gate(gid, "Documentation", "FAILED", ["no README in the project"], "Add a README with how to run it",
                         "file check"))
    else:
        size = len(readme.read_text(encoding="utf-8", errors="replace").strip())
        out.append(_gate(gid, "Documentation", "PASSED" if size >= 200 else "WARNING", [f"{readme.name}: {size} characters"],
                         "None" if size >= 200 else "Expand the README (setup, run, test)", "file check"))
    gid += 1
    out.append(_gate(gid, "Test Coverage", "NOT_EVALUATED", ["line coverage is not measured"], "None", "not evaluated"))
    gid += 1
    out.append(_gate(gid, "Performance", "NOT_EVALUATED", ["no performance measurement is recorded in this report"],
                     "Measure it with the Performance Engineer", "not evaluated"))
    return out


def _sev(findings) -> Dict[str, int]:
    out = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        s = getattr(f, "severity", "")
        if s in out:
            out[s] += 1
    return out


def summary(gate_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    evaluated = [g for g in gate_list if g["status"] in GATE_EVALUATED and g["status"] != "SKIPPED"]
    passed = [g for g in evaluated if g["status"] in GATE_OK]
    return {"evaluated": len(evaluated), "passed": len(passed), "total": len(gate_list),
            "not_evaluated": sum(1 for g in gate_list if g["status"] == "NOT_EVALUATED"),
            "pass_rate": round(100.0 * len(passed) / len(evaluated), 1) if evaluated else None}


def tests(ev: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    v = ev["verification"]
    c = next((x for x in (v.checks if v else []) if x.name == "python_tests"), None)
    if c is None or c.status not in ("PASSED", "FAILED") or not c.counts:
        return None
    passed, failed = c.counts.get("passed", 0), c.counts.get("failed", 0) + c.counts.get("errors", 0)
    return {"total": passed + failed + c.counts.get("skipped", 0), "passed": passed, "failed": failed,
            "skipped": c.counts.get("skipped", 0), "coverage": None, "source": f"verification {v.id}",
            "failing_tests": sorted({t for f in v.failures if f.check == "python_tests" for t in f.failing_tests})}
