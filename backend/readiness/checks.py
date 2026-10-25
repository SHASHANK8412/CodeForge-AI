"""
AIForge Readiness Check Collector - evidence only.

Every check reads a real source and says which; a category without evidence is NOT_AVAILABLE (and is
left out of the score) instead of being assumed:

  Security        latest completed Security Guardian assessment (findings in their current state)
  Testing         latest test run recorded by Autopilot in the Docker sandbox (the project's own tests)
  Performance     latest Performance Engineer baseline run
  Requirements    requirement traces in the project's DNA graph
  Architecture    ADRs recorded by Debate sessions (their content is not judged)
  Code Quality    latest Autopilot analysis (open syntax/quality/maintainability findings) and
                  dependency cycles from the latest Digital Twin graph
  Database        static inspection: database use and migration history (nothing is executed)
  Documentation   static inspection: README
  Deployment      static inspection: Dockerfile (non-root user, health check)
  Observability   static inspection: logging, metrics or tracing instrumentation in the code
  Browser Testing not available: AIForge's browser-testing module does not drive a real browser
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.guardian.service import security_status
from backend.performance.service import global_performance_service
from backend.readiness.models import CheckSeverity, CheckStatus, ReadinessCheck

_logger = logging.getLogger("aiforge.readiness.checks")
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build", ".pytest_cache"}
NO_EVIDENCE_SCORE = 0.0      # NOT_AVAILABLE checks are excluded from the score (see scoring.py)


def project_dir(project_id: str) -> Optional[Path]:
    """The generated project's folder, if it is registered and present (authorization is the caller's job)."""
    try:
        from backend.generation.store import global_generation_store
        from backend.routes.export import _safe_project_dir
        rec = global_generation_store.get(project_id)
        return _safe_project_dir(rec.get("project_path") or "") if rec else None
    except Exception:  # noqa: BLE001 - an unknown project simply has no file evidence
        return None


def _files(root: Path, names, limit: int = 2000) -> List[Path]:
    out = []
    for p in root.rglob("*"):
        if len(out) >= limit:
            break
        rel = p.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts) or p.is_symlink() or not p.is_file():
            continue
        if p.suffix in names or p.name in names:
            out.append(p)
    return out


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")[:200_000]
    except OSError:
        return ""


def _na(cid: str, category: str, name: str, evidence: str, severity=CheckSeverity.MEDIUM, recommendation=None):
    return ReadinessCheck(id=cid, category=category, name=name, status=CheckStatus.NOT_AVAILABLE, severity=severity,
                          score=NO_EVIDENCE_SCORE, evidence=evidence, blocking=False, recommendation=recommendation)


# --- evidence sources -------------------------------------------------------------------------------------------

def latest_test_run(project_id: str) -> Optional[Dict[str, Any]]:
    """The newest real test result Autopilot recorded for the project's code: the after-checks of an applied
    change, otherwise the run's baseline (the project as it was)."""
    from backend.evolution.autopilot.service import global_autopilot_service
    try:
        executions = global_autopilot_service.store.list(project_id, "executions")
    except ValueError:
        return None
    best = None
    for e in executions:
        for c in (e.after if e.applied_to_project else e.baseline):
            if c.check_id == "tests" and c.status in ("passed", "failed") and (best is None or c.finished_at > best[0].finished_at):
                best = (c, e)
    if best is None:
        return None
    c, e = best
    return {"status": c.status, "counts": c.counts, "environment": c.environment, "finished_at": c.finished_at,
            "execution_id": e.id}


def code_quality(project_id: str) -> Optional[Dict[str, Any]]:
    from backend.evolution.autopilot.service import global_autopilot_service
    from backend.twin.service import global_twin_service
    out: Dict[str, Any] = {}
    try:
        analyses = [a for a in global_autopilot_service.store.list(project_id, "analyses") if a.status == "completed"]
    except ValueError:
        analyses = []
    if analyses:
        a = max(analyses, key=lambda x: x.finished_at or "")
        ids = set(a.finding_ids)
        open_ = [f for f in global_autopilot_service.store.list(project_id, "findings") if f.id in ids
                 and f.status.value == "open" and f.category.value in ("syntax", "quality", "maintainability")]
        out.update(analysis_id=a.id, analyzed_at=a.finished_at, open=len(open_),
                   high=sum(1 for f in open_ if f.severity.value in ("critical", "high")),
                   syntax=sum(1 for f in open_ if f.category.value == "syntax"))
    try:
        g = global_twin_service.store.latest_graph(project_id)
    except ValueError:
        g = None
    if g is not None:
        out.update(graph_id=g.id, cycles=len(g.cycles))
    return out or None


def requirement_traces(project_id: str):
    from backend.dna.impact import global_impact_engine
    try:
        return global_impact_engine.trace_requirements(project_id)
    except Exception:  # noqa: BLE001
        return []


def architecture_records(project_id: str):
    from backend.debate.service import global_debate_service
    try:
        return global_debate_service.get_all_adrs(project_id)
    except Exception:  # noqa: BLE001
        return []


# --- the collector ---------------------------------------------------------------------------------------------

class ReadinessCheckCollector:
    def collect_all_checks(self, project_id: str, project: Optional[Path] = None) -> List[ReadinessCheck]:
        _logger.info("[ReadinessChecks] Gathering evidence for project '%s'", project_id)
        root = project or project_dir(project_id)
        return [self.security(project_id), self.testing(project_id), self.browser(), self.performance(project_id),
                self.requirements(project_id), self.architecture(project_id), self.code_quality(project_id),
                self.database(root), self.documentation(root), self.deployment(root), self.observability(root)]

    def security(self, project_id: str) -> ReadinessCheck:
        sec = security_status(project_id)
        if sec["decision"] == "NOT_ASSESSED":
            return _na("chk_sec_01", "Security", "Security Guardian Assessment",
                       "Not assessed: run an assessment in the Security Guardian.", CheckSeverity.HIGH)
        blocked = sec["decision"] == "BLOCK"
        warn = sec["decision"] == "REVIEW_NEEDED" or bool(sec["tools_unavailable"])
        return ReadinessCheck(
            id="chk_sec_01", category="Security", name="Security Guardian Assessment",
            status=CheckStatus.FAIL if blocked else (CheckStatus.WARN if warn else CheckStatus.PASS),
            severity=CheckSeverity.CRITICAL if blocked else (CheckSeverity.MEDIUM if warn else CheckSeverity.LOW),
            score=40.0 if blocked else (85.0 if warn else 100.0),
            evidence=sec["detail"] + ("" if blocked else ". No known blockers is not proof of security."),
            blocking=blocked,
            recommendation="Fix or explicitly accept the open critical/high findings." if blocked else
            "Review the critical/high findings that need a decision in the Security Guardian." if sec["decision"] == "REVIEW_NEEDED" else None)

    def testing(self, project_id: str) -> ReadinessCheck:
        run = latest_test_run(project_id)
        if run is None:
            return _na("chk_test_01", "Testing", "Project Test Suite",
                       "Not run: no test result has been recorded for this project (Autopilot runs the project's tests "
                       "in the Docker sandbox).", CheckSeverity.HIGH)
        counts = run["counts"]
        passed, failed, errors = counts.get("passed", 0), counts.get("failed", 0), counts.get("errors", 0)
        ok = run["status"] == "passed" and passed > 0
        return ReadinessCheck(
            id="chk_test_01", category="Testing", name="Project Test Suite",
            status=CheckStatus.PASS if ok else CheckStatus.FAIL, severity=CheckSeverity.HIGH,
            score=round(100.0 * passed / max(1, passed + failed + errors), 1),
            evidence=f"{passed} passed, {failed} failed, {errors} errors ({run['environment']}; recorded {run['finished_at']}, "
                     f"Autopilot execution {run['execution_id']}). The code may have changed since.",
            blocking=not ok,
            recommendation=None if ok else "Fix the failing tests and run them again.")

    def browser(self) -> ReadinessCheck:
        return _na("chk_browser_01", "Browser Testing", "Browser User Journeys",
                   "Not available: AIForge's browser-testing module does not drive a real browser yet, so it provides no evidence.",
                   CheckSeverity.LOW)

    def performance(self, project_id: str) -> ReadinessCheck:
        perf = global_performance_service.latest_measurement(project_id)
        if perf is None or perf["worst_p95_ms"] is None:
            return _na("chk_perf_01", "Performance", "API Latency Baseline",
                       "Not measured: run a baseline in the Performance Engineer to measure API latency.")
        ok = perf["worst_p95_ms"] < 300 and perf["max_error_rate_pct"] == 0
        return ReadinessCheck(
            id="chk_perf_01", category="Performance", name="API Latency Baseline",
            status=CheckStatus.PASS if ok else CheckStatus.WARN, severity=CheckSeverity.MEDIUM,
            score=100.0 if ok else 75.0,
            evidence=(f"Measured {perf['finished_at']}: worst p95 {perf['worst_p95_ms']} ms on {perf['worst_endpoint']} "
                      f"(target < 300 ms), max error rate {perf['max_error_rate_pct']}% across {perf['endpoints']} endpoint(s)"))

    def requirements(self, project_id: str) -> ReadinessCheck:
        traces = requirement_traces(project_id)
        if not traces:
            return _na("chk_req_01", "Requirements", "Requirement Traceability",
                       "Not available: the project's DNA graph has no requirement traces.")
        done = sum(1 for t in traces if t.status == "IMPLEMENTED")
        score = round(100.0 * done / len(traces), 1)
        return ReadinessCheck(
            id="chk_req_01", category="Requirements", name="Requirement Traceability",
            status=CheckStatus.PASS if score >= 90.0 else CheckStatus.WARN, severity=CheckSeverity.HIGH, score=score,
            evidence=f"{done}/{len(traces)} requirements trace to code in the DNA graph (traceability, not functional proof)")

    def architecture(self, project_id: str) -> ReadinessCheck:
        adrs = architecture_records(project_id)
        if not adrs:
            return _na("chk_arch_01", "Architecture", "Architecture Decision Records",
                       "Not available: no architecture decisions have been recorded for this project.", CheckSeverity.LOW)
        return ReadinessCheck(
            id="chk_arch_01", category="Architecture", name="Architecture Decision Records",
            status=CheckStatus.PASS, severity=CheckSeverity.LOW, score=100.0,
            evidence=f"{len(adrs)} architecture decision record(s) recorded (their content is not evaluated)")

    def code_quality(self, project_id: str) -> ReadinessCheck:
        q = code_quality(project_id)
        if q is None:
            return _na("chk_code_01", "Code Quality", "Static Analysis and Dependency Graph",
                       "Not available: run an Autopilot analysis (and a Digital Twin graph for dependency cycles).")
        parts, status, score = [], CheckStatus.PASS, 100.0
        if "open" in q:
            parts.append(f"{q['open']} open quality/maintainability finding(s), {q['high']} high, {q['syntax']} syntax "
                         f"(Autopilot analysis {q['analysis_id']}, {q['analyzed_at']})")
            if q["syntax"]:
                status, score = CheckStatus.FAIL, 50.0
            elif q["high"]:
                status, score = CheckStatus.WARN, 75.0
            elif q["open"]:
                status, score = CheckStatus.WARN, 90.0
        if "cycles" in q:
            parts.append(f"{q['cycles']} dependency cycle(s) (Digital Twin graph {q['graph_id']})")
            if q["cycles"] and status == CheckStatus.PASS:
                status, score = CheckStatus.WARN, 85.0
        return ReadinessCheck(id="chk_code_01", category="Code Quality", name="Static Analysis and Dependency Graph",
                              status=status, severity=CheckSeverity.MEDIUM, score=score, evidence="; ".join(parts),
                              blocking=bool(q.get("syntax")))

    def database(self, root: Optional[Path]) -> ReadinessCheck:
        name = "Database Schema and Migrations"
        if root is None:
            return _na("chk_db_01", "Database", name, "Not available: the project's files could not be found.")
        py = _files(root, {".py"})
        text = "\n".join(_read(p) for p in py)
        if not re.search(r"\b(sqlalchemy|sqlite3|psycopg2?|pymongo|motor|asyncpg|tortoise|peewee)\b", text):
            return _na("chk_db_01", "Database", name, "Not applicable: no database library is used in the Python code.",
                       CheckSeverity.LOW)
        migrations = [p for p in py if "versions" in p.parts and ("alembic" in p.parts or "migrations" in p.parts)]
        if migrations:
            return ReadinessCheck(id="chk_db_01", category="Database", name=name, status=CheckStatus.PASS,
                                  severity=CheckSeverity.MEDIUM, score=100.0,
                                  evidence=f"{len(migrations)} migration file(s) found (static inspection; migrations were not executed)")
        return ReadinessCheck(id="chk_db_01", category="Database", name=name, status=CheckStatus.WARN,
                              severity=CheckSeverity.MEDIUM, score=70.0,
                              evidence="A database is used but there is no migration history (static inspection): schema "
                                       "changes would have to be applied by hand.",
                              recommendation="Add migrations (for example Alembic) before changing the schema in production.")

    def documentation(self, root: Optional[Path]) -> ReadinessCheck:
        name = "Project Documentation"
        if root is None:
            return _na("chk_doc_01", "Documentation", name, "Not available: the project's files could not be found.", CheckSeverity.LOW)
        readmes = sorted(p for p in root.glob("README*") if p.is_file())
        if not readmes:
            return ReadinessCheck(id="chk_doc_01", category="Documentation", name=name, status=CheckStatus.WARN,
                                  severity=CheckSeverity.LOW, score=50.0, evidence="No README at the project root (static inspection).",
                                  recommendation="Add a README with setup, configuration and run instructions.")
        text = _read(readmes[0])
        topics = [s for s in ("install", "run", "test", "environment", "config", "deploy") if s in text.lower()]
        ok = len(text) >= 300 and len(topics) >= 2
        return ReadinessCheck(id="chk_doc_01", category="Documentation", name=name,
                              status=CheckStatus.PASS if ok else CheckStatus.WARN, severity=CheckSeverity.LOW,
                              score=100.0 if ok else 70.0,
                              evidence=f"{readmes[0].name}: {len(text)} characters, mentions {', '.join(topics) or 'no setup topics'} "
                                       "(static inspection; accuracy not checked)",
                              recommendation=None if ok else "Document installation, configuration and how to run and test the app.")

    def deployment(self, root: Optional[Path]) -> ReadinessCheck:
        name = "Container Configuration"
        if root is None:
            return _na("chk_dep_01", "Deployment", name, "Not available: the project's files could not be found.", CheckSeverity.LOW)
        dockerfiles = _files(root, {"Dockerfile"}, limit=20)
        if not dockerfiles:
            return ReadinessCheck(id="chk_dep_01", category="Deployment", name=name, status=CheckStatus.WARN,
                                  severity=CheckSeverity.LOW, score=60.0, evidence="No Dockerfile (static inspection).",
                                  recommendation="Add a Dockerfile that runs as a non-root user with a health check.")
        issues = []
        for d in dockerfiles:
            t = _read(d)
            users = re.findall(r"(?im)^\s*USER\s+(\S+)", t)
            rel = d.relative_to(root).as_posix()
            if not users or users[-1] in ("root", "0"):
                issues.append(f"{rel} runs as root")
            if not re.search(r"(?im)^\s*HEALTHCHECK\s", t):
                issues.append(f"{rel} has no HEALTHCHECK")
        return ReadinessCheck(id="chk_dep_01", category="Deployment", name=name,
                              status=CheckStatus.WARN if issues else CheckStatus.PASS, severity=CheckSeverity.LOW,
                              score=100.0 - 15.0 * min(len(issues), 4),
                              evidence=(f"{len(dockerfiles)} Dockerfile(s): " + ("; ".join(issues) if issues else
                                        "non-root user and health check present")) + " (static inspection; not built)",
                              recommendation="Run as a non-root user and add a HEALTHCHECK." if issues else None)

    def observability(self, root: Optional[Path]) -> ReadinessCheck:
        name = "Logging, Metrics and Tracing"
        if root is None:
            return _na("chk_otel_01", "Observability", name, "Not available: the project's files could not be found.", CheckSeverity.LOW)
        text = "\n".join(_read(p) for p in _files(root, {".py", ".js", ".ts"}))
        found = [label for label, pat in (("tracing (OpenTelemetry)", r"opentelemetry"),
                                          ("metrics (Prometheus)", r"prometheus|/metrics"),
                                          ("logging", r"logging\.getLogger|structlog|winston|pino"))
                 if re.search(pat, text)]
        return ReadinessCheck(id="chk_otel_01", category="Observability", name=name,
                              status=CheckStatus.PASS if len(found) >= 2 else CheckStatus.WARN, severity=CheckSeverity.LOW,
                              score=100.0 if len(found) >= 2 else 60.0,
                              evidence=("Found " + ", ".join(found) if found else "No logging, metrics or tracing instrumentation found")
                                       + " in the code (static inspection)")


global_readiness_check_collector = ReadinessCheckCollector()
