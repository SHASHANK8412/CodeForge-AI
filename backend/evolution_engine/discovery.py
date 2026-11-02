"""
Improvement discovery from evidence AIForge already produces (no new scanners):

  Performance Engineer  static N+1 detection (a query inside a loop, with its endpoint) and the latest
                        measured baseline run (latency of that endpoint)
  Security Guardian     verified, open findings (listed; they are remediated through the Guardian)
  Engineering Memory    past experiments on the same file / category

Only N+1 opportunities on a measurable endpoint can be experimented on in this version; everything else
is listed with the reason. Expected benefits are predictions until an experiment measures them.
"""

import hashlib
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.evolution_engine.models import Opportunity

SEVERITY = {"high": 1.0, "medium": 0.6, "low": 0.3}
CONFIDENCE = {"high": 1.0, "medium": 0.6, "low": 0.3}
DEFAULT_CRITERIA = {"severity": 0.3, "expected_benefit": 0.3, "effort": 0.15, "uncertainty": 0.15, "regression_risk": 0.1}


def opportunity_id(project_id: str, category: str, file: Optional[str], endpoint: Optional[str], detail: str) -> str:
    return "op_" + hashlib.sha1(f"{project_id}|{category}|{file}|{endpoint}|{detail[:120]}".encode()).hexdigest()[:14]


def data_access(source: str) -> str:
    if re.search(r"\bsqlalchemy\b|\bSession\b|\.query\(", source):
        return "sqlalchemy"
    if re.search(r"\bsqlite3\b|\bpsycopg2?\b|\basyncpg\b|\.execute\(", source):
        return "raw_sql"
    return "unknown"


def _dependents(project: Path, rel: str) -> List[str]:
    try:
        from backend.twin.graph import build_graph
        from backend.twin.index import GraphIndex
        from backend.twin.models import GraphAnalysis
        b = build_graph(project, deadline_seconds=20)
        index = GraphIndex(GraphAnalysis(id="tmp", project_id="tmp", user_id="tmp", nodes=list(b.nodes.values()),
                                         edges=list(b.edges.values())))
        return [p for p, _ in index.dependents(rel)][:20]
    except Exception:  # noqa: BLE001 - context is optional
        return []


def _measured(project_id: str) -> Dict[str, Dict[str, Any]]:
    """'METHOD /path' -> latest measured stats (Performance Engineer baseline run)."""
    from backend.performance.engineer.service import global_performance_engineer
    try:
        run = global_performance_engineer.store.latest(project_id, "runs", "completed")
    except ValueError:
        return {}
    if run is None or run.measurement is None or run.measurement.status != "measured":
        return {}
    return {f"{e.method} {e.path}": {"median_ms": e.median_ms, "p95_ms": e.p95_ms, "requests": e.requests,
                                      "run_id": run.id, "finished_at": run.finished_at} for e in run.measurement.endpoints}


def prioritize(op: Opportunity, criteria: Optional[Dict[str, float]] = None) -> None:
    """Weighted 0-100 priority with every factor shown (all inputs are qualitative, so is the number)."""
    c = {**DEFAULT_CRITERIA, **(criteria or {})}
    measured = any(e["kind"] == "measured" for e in op.evidence)
    factors = {
        "severity": SEVERITY.get(next((e.get("severity") for e in op.evidence if e.get("severity")), "low"), 0.3),
        "expected_benefit": 0.9 if measured else 0.5,             # a measured slow endpoint makes a gain more likely
        "effort": 0.8 if op.file and op.experimentable else 0.3,   # single-file change vs. anything larger
        "uncertainty": CONFIDENCE.get(op.confidence, 0.3),         # higher = less uncertain
        "regression_risk": 0.6,                                    # data-access changes can change results
    }
    total = sum(c.values()) or 1.0
    op.priority_factors = {k: round(v, 2) for k, v in factors.items()}
    op.priority = round(100 * sum(factors[k] * c[k] for k in factors) / total, 1)


def discover(project_id: str, project: Path, criteria: Optional[Dict[str, float]] = None) -> List[Opportunity]:
    from backend.evolution_engine.memory import related
    from backend.execution.preview_manager import backend_entry
    from backend.execution.project_runner import global_project_runner
    from backend.performance.engineer.static import project_findings
    project = Path(project).resolve()
    raws, _ = project_findings(project)
    measured = _measured(project_id)
    fastapi = backend_entry(project) is not None
    # the test runner prepares the folder it inspects (package markers): ask it about a disposable copy,
    # so discovery never writes into the project
    from backend.evolution.autopilot.workspace import create_workspace, discard_workspace
    copy = create_workspace(project, prefix="aiforge_evolve_probe_")
    try:
        test_cmd, _ = global_project_runner.select_safe_command(copy)
    finally:
        discard_workspace(copy)
    has_tests = bool(test_cmd) and "compileall" not in test_cmd
    out: List[Opportunity] = []
    for f in raws:
        if f["category"] != "n_plus_one":
            continue
        endpoint = f.get("endpoint")
        source = (project / f["file"]).read_text(encoding="utf-8", errors="replace") if f.get("file") else ""
        evidence = [{"kind": "static", "source": "Performance Engineer (Python ast)", "severity": f["severity"],
                     "detail": f"{f['file']}:{f['line']}: {f['evidence']}"}]
        if endpoint and endpoint in measured:
            m = measured[endpoint]
            evidence.append({"kind": "measured", "source": f"Performance Engineer run {m['run_id']}",
                             "detail": f"{endpoint}: median {m['median_ms']} ms, p95 {m['p95_ms']} ms over {m['requests']} requests "
                                       f"({m['finished_at']})"})
        reason = None
        if not endpoint:
            reason = "the query loop is not reached from a route, so there is nothing to measure"
        elif not endpoint.startswith("GET ") or "{" in endpoint:
            reason = "only GET endpoints without path parameters can be measured with an equivalent workload"
        elif not fastapi:
            reason = "the project is not a FastAPI app that the sandbox can start"
        elif not has_tests:
            reason = "the project has no tests, so a candidate's correctness cannot be checked"
        op = Opportunity(
            id=opportunity_id(project_id, "n_plus_one", f["file"], endpoint, f["evidence"]), project_id=project_id,
            category="n_plus_one", title=f["title"], evidence=evidence, file=f["file"], line=f["line"], endpoint=endpoint,
            components=[f["file"]] + _dependents(project, f["file"]),
            hypothesis=(f"{endpoint or 'The endpoint'} issues one query per row; loading the related rows in one query "
                        "will lower its latency without changing its response."),
            expected_benefit="prediction: lower median latency that grows less with the number of rows (not measured yet)",
            possible_regressions=["a changed response (missing rows with no related data, different order or fields)",
                                  "higher memory use when all related rows are loaded at once",
                                  "SQL built from strings instead of bound parameters"],
            confidence=f["confidence"], validation=f["validation"] + "; the project's tests and a security re-check must pass",
            experimentable=reason is None, not_experimentable_reason=reason)
        op.history = related(project_id, op.category, {"file": op.file, "data_access": data_access(source),
                                                       "endpoint": endpoint})
        prioritize(op, criteria)
        out.append(op)
    # verified security findings: listed with their evidence, remediated through the Security Guardian
    try:
        from backend.guardian.service import global_security_guardian
        for g in global_security_guardian.store.list(project_id, "findings"):
            if g.state == "verified" and "resolved_at" not in g.context:
                op = Opportunity(
                    id=opportunity_id(project_id, "security", g.file, g.route, g.rule_id), project_id=project_id,
                    category="security", title=g.title, file=g.file, line=g.line, endpoint=g.route,
                    evidence=[{"kind": "measured", "source": "Security Guardian safe verification", "severity": g.severity,
                               "detail": (g.verification.conclusion if g.verification else "")}],
                    hypothesis=g.remediation, expected_benefit="the issue no longer reproduces (verified by the Guardian gate)",
                    confidence="high", validation="Security Guardian re-verification", experimentable=False,
                    not_experimentable_reason="remediate it from the Security Guardian (its gate re-verifies the fix); "
                                              "multi-candidate security experiments are not implemented yet")
                prioritize(op, criteria)
                out.append(op)
    except ValueError:
        pass
    return sorted(out, key=lambda o: (not o.experimentable, -o.priority))
