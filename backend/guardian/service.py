"""
AIForge Security Guardian service.

  assessment     static rules (ast, patterns), Bandit, secret scanning, pip-audit / npm audit, config rules;
                 de-duplicated and placed in the architecture (Digital Twin). States: queued -> analyzing ->
                 completed | failed | aborted. Unavailable tools are listed, never treated as clean.
  verification   only after explicit approval: benign requests against a disposable copy in the isolated
                 sandbox (verify.py) -> verified | not_reproduced | verification_unavailable
  remediation    an Autopilot plan (origin "security"): a model fix limited to the finding's file plus a
                 templated regression test; approval, isolated copy, correctness checks (tests in Docker,
                 including the new test), then the security gate: the same verification on the original and
                 the changed copy (or a static re-check when no safe verification exists). Applied only on
                 "improved"; changes needing a design decision or a dependency upgrade go to a person.
"""

import logging
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from backend.evolution.autopilot.models import Plan, PlanTask, now_iso
from backend.evolution.autopilot.redact import redact
from backend.evolution.autopilot.store import AutopilotStore
from backend.guardian import correlate, regression, rules_py, scanners
from backend.guardian.models import Assessment, Finding, Gate, ToolRun, Verification
from backend.guardian.verify import STATE_OF, verify

_logger = logging.getLogger("aiforge.guardian")
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build", ".next", ".pytest_cache",
             ".ruff_cache", ".mypy_cache", "coverage", ".aiforge_checkpoints"}
MAX_FILES, MAX_BYTES = 4000, 512 * 1024
ASSESSMENT_DEADLINE = 900
AUTO_REMEDIABLE = {"PY-SQLI", "PY-SENSITIVE-RESPONSE", "PY-PATH-TRAVERSAL", "PY-CORS", "PY-OPEN-REDIRECT",
                   "PY-COOKIE-FLAGS", "PY-DEBUG", "PY-CMDI", "PY-EVAL", "PY-DESERIALIZE", "PY-HARDCODED-KEY",
                   "PY-JWT-NO-VERIFY", "PY-PREDICTABLE-TOKEN", "PY-MISSING-AUTH", "PY-ERROR-DETAIL"}
HUMAN_REVIEW = {
    "dependencies": "dependency upgrades can break behaviour: review the advisory and upgrade deliberately",
    "PY-WEAK-HASH": "changing password hashing invalidates stored hashes: needs a migration decision",
    "PY-TRUSTED-ROLE": "access-control design decision",
    "SECRET-HARDCODED": "the credential must be rotated by a person; code changes alone do not fix a leaked secret",
    "SECRET-PRIVATE-KEY": "the key must be revoked and replaced by a person",
    "SECRET-ENV-FILE": "the values must be rotated and the file removed from the project by a person",
}


class GuardianError(ValueError):
    pass


class Busy(RuntimeError):
    pass


class GuardianStore(AutopilotStore):
    KINDS = {"assessments": Assessment, "findings": Finding, "gates": Gate}
    PRUNE = (("assessments", 30, "created_at"), ("gates", 50, "created_at"))
    ENV_DIR = "AIFORGE_GUARDIAN_DIR"
    DEFAULT_ROOT = Path(__file__).resolve().parents[1] / "data" / "guardian"

    def latest(self, project_id: str, status: Optional[str] = None) -> Optional[Assessment]:
        items = [a for a in self.list(project_id, "assessments") if not a.verification_requested
                 and (status is None or a.status == status)]
        return max(items, key=lambda a: a.created_at, default=None)


def read_sources(project: Path) -> Dict[str, str]:
    """Text files of the project, including dot-env files (secret detection), bounded; no symlinks."""
    project = Path(project).resolve()
    out: Dict[str, str] = {}
    count = 0
    for p in sorted(project.rglob("*")):
        rel = p.relative_to(project)
        if any(part in SKIP_DIRS for part in rel.parts) or p.is_symlink() or not p.is_file():
            continue
        count += 1
        if count > MAX_FILES:
            break
        if p.stat().st_size > MAX_BYTES:
            continue
        try:
            out[rel.as_posix()] = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
    return out


def analyze(project_id: str, project: Path, should_stop: Callable[[], bool] = lambda: False,
            on_event: Callable[[str], None] = lambda s: None):
    """(findings, tool runs, coverage) for a project. Read-only."""
    project = Path(project).resolve()
    files = read_sources(project)
    runs: List[ToolRun] = []
    raws: List[Dict[str, Any]] = []
    uses_auth, middleware = rules_py.project_auth_facts(files)
    on_event("python rules")
    py = [rel for rel in files if rel.endswith(".py") and not Path(rel).name.startswith("test_") and "/tests/" not in f"/{rel}"]
    for rel in py:
        raws += [dict(r, source="guardian-ast") for r in rules_py.analyze(rel, files[rel], uses_auth, middleware)]
    runs.append(ToolRun(tool="Guardian Python rules (ast)", status="ran", detail=f"{len(py)} files"))
    steps = [("bandit", lambda: scanners.bandit(project)), ("secrets", lambda: scanners.secrets(project, files)),
             ("javascript", lambda: scanners.js_rules(files)), ("configuration", lambda: scanners.config_rules(files)),
             ("pip-audit", lambda: scanners.pip_audit(project)), ("npm audit", lambda: scanners.npm_audit(project))]
    for name, step in steps:
        if should_stop():
            raise InterruptedError("aborted")
        on_event(name)
        try:
            found, run = step()
        except Exception as e:  # noqa: BLE001 - one broken scanner does not stop the others
            found, run = [], ToolRun(tool=name, status="error", detail=redact(f"{type(e).__name__}: {e}", 300))
        raws += found
        runs.append(run)
    on_event("correlating with the Digital Twin graph")
    context = correlate.Context(project)
    context.protected_routes = correlate.protected_routes(files)
    context.all_protected = middleware
    lines_of = {rel: src.splitlines() for rel, src in files.items()}
    findings = correlate.build(project_id, raws, lines_of, context)
    langs = sorted({Path(r).suffix for r in files if Path(r).suffix in (".py", ".js", ".jsx", ".ts", ".tsx")})
    coverage = {
        "files_read": len(files), "languages": langs,
        "tools": {r.tool: r.status for r in runs},
        "not_covered": [r.tool + ": " + r.detail for r in runs if r.status != "ran"] + [
            "data flow is followed only inside one function (no cross-function taint)",
            "JavaScript/TypeScript rules are pattern-based (no data-flow proof)",
            "business-logic flaws, authorization rules between users, and rate limiting are not analysed",
        ],
        "auth": {"project_uses_auth_dependencies": uses_auth, "auth_middleware": middleware,
                 "protected_routes": sorted(context.protected_routes)},
    }
    return findings, runs, coverage


class SecurityGuardian:
    def __init__(self, store: Optional[GuardianStore] = None, autopilot=None, background: bool = True):
        self.store = store or GuardianStore()
        self._autopilot = autopilot
        self.background = background
        self._active: Dict[str, str] = {}
        self._lock = threading.Lock()
        if background:
            try:
                self.store.mark_interrupted()
            except Exception as e:  # noqa: BLE001
                _logger.warning("Security Guardian: could not check for interrupted jobs: %s", e)

    @property
    def autopilot(self):
        if self._autopilot is None:
            from backend.evolution.autopilot.service import global_autopilot_service
            self._autopilot = global_autopilot_service
        return self._autopilot

    def _start(self, project_id, job_id, kind, target):
        with self._lock:
            if project_id in self._active:
                self.store.delete(project_id, kind, job_id)
                raise Busy(f"another security job ({self._active[project_id]}) is running for this project")
            self._active[project_id] = job_id

        def run():
            try:
                target()
            finally:
                with self._lock:
                    self._active.pop(project_id, None)
        if self.background:
            threading.Thread(target=run, name=f"guardian-{job_id}", daemon=True).start()
        else:
            run()

    def active_job(self, project_id: str) -> Optional[str]:
        with self._lock:
            return self._active.get(project_id)

    @staticmethod
    def _audit(a: Assessment, action: str, **details):
        a.audit.append({"at": now_iso(), "action": action, **{k: redact(str(v), 400) for k, v in details.items()}})

    # --- assessment -----------------------------------------------------------------------------------

    def start(self, project_id: str, project_dir: Path, user_id: str) -> Assessment:
        a = Assessment(id="sga_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id)
        self._audit(a, "created", user=user_id)
        self.store.put(project_id, "assessments", a)
        self._start(project_id, a.id, "assessments", lambda: self._run(project_id, a.id, Path(project_dir)))
        return self.store.get(project_id, "assessments", a.id)

    def _run(self, project_id: str, aid: str, project: Path) -> None:
        deadline = time.monotonic() + ASSESSMENT_DEADLINE

        def stopped():
            a = self.store.get(project_id, "assessments", aid)
            return bool(a and a.abort_requested) or time.monotonic() > deadline

        def event(text):
            self.store.update(project_id, "assessments", aid, lambda a: self._audit(a, text))
        self.store.update(project_id, "assessments", aid,
                          lambda a: (setattr(a, "status", "analyzing"), setattr(a, "started_at", now_iso())))
        try:
            findings, runs, coverage = analyze(project_id, project, stopped, event)
            previous = {f.id: f for f in self.store.list(project_id, "findings")}
            merged = correlate.merge_history(previous, findings)
            with self.store._lock:
                data = self.store._load(project_id)
                data["findings"] = {fid: f.model_dump(mode="json") for fid, f in merged.items()}
                self.store._save(project_id, data)

            def done(a: Assessment):
                a.status, a.finished_at = "completed", now_iso()
                a.tools, a.coverage = runs, coverage
                a.finding_ids = [f.id for f in findings]
                a.summary = correlate.summarize(findings)
                self._audit(a, "completed", findings=len(findings))
            self.store.update(project_id, "assessments", aid, done)
            from backend.time_machine.recorder import emit
            summary = correlate.summarize(findings)
            emit(project_id, "security_finding", "Security Guardian",
                 f"assessment: {summary['open']} open finding(s), {summary['critical_high_open']} critical/high",
                 "failure" if summary["critical_high_open"] else "success", task_id=aid, refs={"assessment_id": aid},
                 project_dir=project, data={"summary": summary, "tools": {r.tool: r.status for r in runs},
                                            "findings": [{"id": f.id, "rule": f.rule_id, "severity": f.severity,
                                                          "file": f.file, "line": f.line, "state": f.state}
                                                         for f in findings[:100]]})
        except InterruptedError:
            self.store.update(project_id, "assessments", aid, lambda a: (
                setattr(a, "status", "aborted"), setattr(a, "finished_at", now_iso()),
                setattr(a, "error", "aborted (by the user or the time limit)")))
        except Exception as e:  # noqa: BLE001
            _logger.exception("Security assessment %s failed", aid)
            msg = redact(f"{type(e).__name__}: {e}", 800)
            self.store.update(project_id, "assessments", aid, lambda a: (
                setattr(a, "status", "failed"), setattr(a, "finished_at", now_iso()), setattr(a, "error", msg)))

    def abort(self, project_id: str, aid: str) -> Optional[Assessment]:
        def change(a: Assessment):
            if a.status in ("queued", "analyzing", "verifying"):
                a.abort_requested = True
                self._audit(a, "abort requested")
        return self.store.update(project_id, "assessments", aid, change)

    # --- verification ------------------------------------------------------------------------------------

    def start_verification(self, project_id: str, project_dir: Path, user_id: str, finding_ids: List[str],
                           approved: bool) -> Assessment:
        if not approved:
            raise GuardianError("verification runs requests against a disposable copy of the app: approve it explicitly")
        findings = [self.store.get(project_id, "findings", i) for i in finding_ids]
        if any(f is None for f in findings) or not findings:
            raise GuardianError("unknown finding id(s)")
        job = Assessment(id="sgv_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id, status="queued",
                         verification_requested=True, verification_ids=finding_ids)
        self._audit(job, "verification approved", user=user_id, findings=finding_ids)
        self.store.put(project_id, "assessments", job)
        for f in findings:
            self.store.update(project_id, "findings", f.id, lambda x: setattr(x, "state", "verification_in_progress"))
        self._start(project_id, job.id, "assessments", lambda: self._verify(project_id, job.id, Path(project_dir), findings))
        return self.store.get(project_id, "assessments", job.id)

    def _verify(self, project_id: str, jid: str, project: Path, findings: List[Finding]) -> None:
        def stopped():
            j = self.store.get(project_id, "assessments", jid)
            return bool(j and j.abort_requested)
        self.store.update(project_id, "assessments", jid, lambda a: (setattr(a, "status", "verifying"), setattr(a, "started_at", now_iso())))
        results: Dict[str, Verification] = {}
        error = None
        try:
            results = verify(project, findings, stopped,
                             lambda t: self.store.update(project_id, "assessments", jid, lambda a: self._audit(a, t)))
        except Exception as e:  # noqa: BLE001 - recorded on the job; the findings keep their previous state
            _logger.exception("Security verification %s failed", jid)
            error = redact(f"{type(e).__name__}: {e}", 800)
        finally:
            for f in findings:
                v = results.get(f.id)

                def apply(x: Finding, v=v, f=f):
                    if v is None:
                        x.state = f.state if f.state != "verification_in_progress" else "detected"
                        return
                    x.verification = v
                    x.state = STATE_OF.get(v.status, "detected")
                    x.last_verified = now_iso()
                    x.priority, x.priority_reasons = correlate.prioritize(x)
                self.store.update(project_id, "findings", f.id, apply)
            outcome = "failed" if error else "aborted" if stopped() else "completed"
            from backend.time_machine.recorder import emit
            emit(project_id, "security_verification", "Security Guardian",
                 f"verification {outcome}: " + ", ".join(f"{k}: {v.status}" for k, v in results.items()),
                 "error" if error else "cancelled" if outcome == "aborted" else "info", task_id=jid,
                 refs={"verification_id": jid}, project_dir=project, error=error,
                 data={"results": {k: {"status": v.status, "conclusion": v.conclusion} for k, v in results.items()}})
            self.store.update(project_id, "assessments", jid, lambda a: (
                setattr(a, "status", outcome), setattr(a, "finished_at", now_iso()), setattr(a, "error", error),
                setattr(a, "summary", {k: (results[k].status if k in results else "not run") for k in a.verification_ids})))

    def accept_risk(self, project_id: str, finding_id: str, user_id: str, note: str) -> Finding:
        if not note.strip():
            raise GuardianError("explain why the risk is accepted")

        def change(f: Finding):
            f.state, f.accepted_by, f.accepted_note = "accepted_risk", user_id, note.strip()[:500]
        f = self.store.update(project_id, "findings", finding_id, change)
        if f is None:
            raise KeyError(finding_id)
        from backend.time_machine.recorder import emit
        emit(project_id, "approval_granted", f"user {user_id}", f"risk accepted: {f.title}", "success",
             task_id=finding_id, refs={"finding_id": finding_id}, data={"note": f.accepted_note, "rule": f.rule_id})
        return f

    # --- remediation ---------------------------------------------------------------------------------------

    def create_plan(self, project_id: str, project_dir: Path, user_id: str, finding_id: str) -> Plan:
        from backend.evolution.autopilot.plans import STRATEGY_AGENT
        f = self.store.get(project_id, "findings", finding_id)
        if f is None:
            raise KeyError(finding_id)
        reason = HUMAN_REVIEW.get(f.rule_id) or HUMAN_REVIEW.get(f.category)
        if reason or f.rule_id not in AUTO_REMEDIABLE:
            raise GuardianError("needs human review: " + (reason or "no safe automatic remediation for this rule"))
        if f.rule_id == "PY-MISSING-AUTH" and f.confidence != "high":
            raise GuardianError("needs human review: whether this route should be public is a design decision")
        if f.state in ("fix_verified", "accepted_risk") or not f.file or not f.file.endswith(".py"):
            raise GuardianError(f"cannot remediate a finding that is '{f.state}' or not in a Python file")
        open_plans = [p for p in self.autopilot.store.list(project_id, "plans") if p.origin == "security"
                      and p.origin_ref == f.id and p.status.value in ("awaiting_approval", "approved", "running", "draft")]
        if open_plans:
            raise GuardianError(f"the finding already has an open plan ({open_plans[0].id})")
        test = regression.generate(Path(project_dir), f)
        evidence = "; ".join(e.detail for e in f.evidence)[:600]
        request = (f"Security fix ({', '.join(f.references) or f.category}). {f.title}\nWhere: {f.file}:{f.line}"
                   + (f" ({f.route})" if f.route else "") + f"\nEvidence (redacted): {evidence}\n"
                   + (f"Verified by a safe test: {f.verification.conclusion}\n" if f.verification and f.state == "verified" else "")
                   + f"Fix: {f.remediation}\nKeep the API contract: same routes, parameters, status codes and response "
                   "fields for legitimate requests (except credential fields that must not be returned). Never weaken "
                   "authentication, validation or tests; do not add new dependencies.")
        tasks = [PlanTask(id="t1", title=f.title[:120], finding_ids=[], files=[f.file], strategy="model",
                          agent=STRATEGY_AGENT["model"], modification=f.remediation, request=redact(request))]
        files = [f.file]
        if test:
            tasks.append(PlanTask(id="t2", title="security regression test", finding_ids=[], files=[test[0]],
                                  strategy="write_files", agent=STRATEGY_AGENT["write_files"],
                                  modification=f"add {test[0]} (templated; must pass after the fix)", contents={test[0]: test[1]}))
            files.append(test[0])
        plan = Plan(
            id="pln_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id, objective=f"Security: {f.title}",
            finding_ids=[], tasks=tasks, expected_files=files,
            agents=sorted({t.agent for t in tasks} | {"Security gate (re-verification)"}),
            checks=["python_syntax", "quality_gate", "security_static", "tests (incl. the security regression test)",
                    "security re-check"],
            risks=["The fix can change behaviour; the project's tests and the API contract must still hold.",
                   "If the finding cannot be reproduced before the change, the fix cannot be verified (reported as inconclusive)."]
            + (["Moving a hardcoded key out of the code does not undo the leak: rotate the key (a person must do this)."]
               if f.rule_id == "PY-HARDCODED-KEY" else []),
            assumptions=[f"Created by the Security Guardian from finding {f.id} ({f.state}); applied only if the "
                         "correctness checks pass and the issue no longer shows."],
            approval_required=["Apply the security fix and the regression test if all gates pass"],
            completion_criteria=["the security regression test passes in the Docker sandbox" if test else
                                 "no templated regression test exists for this rule (static re-check only)",
                                 "the same safe verification no longer shows the issue" if f.verifiable else
                                 "a static re-check no longer detects it", "no correctness regression"],
            origin="security", origin_ref=f.id, security_review_required=f.category == "auth")
        self.autopilot.store.put(project_id, "plans", plan)
        return plan

    def gate(self, plan: Plan, project: Path, workspace: Path, execution_id: str, should_stop: Callable[[], bool],
             on_stage: Optional[Callable[[str, str], None]] = None) -> Gate:
        f = self.store.get(plan.project_id, "findings", plan.origin_ref or "")
        g = Gate(id=execution_id, project_id=plan.project_id, finding_id=plan.origin_ref or "")
        event = on_stage or (lambda a, b: None)
        if f is None:
            g.reasons = ["the finding was not found"]
            self.store.put(plan.project_id, "gates", g)
            return g
        if f.verifiable:
            before = verify(project, [f], should_stop, lambda t: event("original", t)).get(f.id)
            after = verify(workspace, [f], should_stop, lambda t: event("changed copy", t)).get(f.id)
            g.original, g.changed = before, after
            if before is None or after is None or "unavailable" in (before.status, after.status) or "error" in (before.status, after.status):
                g.decision, g.reasons = "not_measured", ["the verification could not run on both versions"]
            elif before.status == "verified" and after.status == "not_reproduced":
                g.decision = "improved"
                g.reasons = [f"before: {before.conclusion}", f"after: {after.conclusion}"]
            elif before.status != "verified":
                g.decision = "inconclusive"
                g.reasons = [f"the issue did not reproduce on the original ({before.conclusion}), so the fix cannot be verified"]
            else:
                g.decision, g.reasons = "inconclusive", [f"the issue still reproduces after the change: {after.conclusion}"]
        else:
            # no safe dynamic test exists: re-run the static analysis on the changed copy
            before_ids = {x.rule_id + "|" + (x.file or "") for x in analyze(plan.project_id, project)[0]}
            after_findings = analyze(plan.project_id, workspace)[0]
            after_ids = {x.rule_id + "|" + (x.file or "") for x in after_findings}
            key = f.rule_id + "|" + (f.file or "")
            new_serious = [x for x in after_findings if x.rule_id + "|" + (x.file or "") not in before_ids
                           and x.severity in ("critical", "high") and x.file in plan.expected_files]
            if new_serious:
                g.decision, g.reasons = "regressed", [f"the change introduced: {x.title} ({x.file}:{x.line})" for x in new_serious]
            elif key not in after_ids:
                g.decision, g.reasons = "improved", [f"static re-check: '{f.rule_id}' is no longer detected in {f.file} "
                                                     "(no safe dynamic verification exists for this rule)"]
            else:
                g.decision, g.reasons = "inconclusive", [f"static re-check: '{f.rule_id}' is still detected in {f.file}"]
        self.store.put(plan.project_id, "gates", g)
        if g.decision == "improved":
            state = "fix_verified" if f.verifiable else "fixed"
            self.store.update(plan.project_id, "findings", f.id, lambda x: (
                setattr(x, "state", state), setattr(x, "last_verified", now_iso()),
                setattr(x, "verification", g.changed or x.verification)))
        return g

    # --- reports ---------------------------------------------------------------------------------------------

    def compare(self, project_id: str, first: str, second: str) -> Dict[str, Any]:
        a, b = self.store.get(project_id, "assessments", first), self.store.get(project_id, "assessments", second)
        if a is None or b is None:
            raise KeyError(first if a is None else second)
        sa, sb = set(a.finding_ids), set(b.finding_ids)
        all_ = {f.id: f for f in self.store.list(project_id, "findings")}
        brief = lambda ids: [{"id": i, "title": all_[i].title if i in all_ else i, "severity": all_[i].severity if i in all_ else None}  # noqa: E731
                             for i in sorted(ids)]
        return {"first": {"id": a.id, "created_at": a.created_at, "summary": a.summary},
                "second": {"id": b.id, "created_at": b.created_at, "summary": b.summary},
                "new": brief(sb - sa), "resolved": brief(sa - sb), "recurring": brief(sa & sb)}

    def report(self, project_id: str, fmt: str = "markdown") -> Any:
        a = self.store.latest(project_id, "completed")
        if a is None:
            raise KeyError("no completed assessment")
        findings = sorted([f for f in self.store.list(project_id, "findings") if f.id in a.finding_ids],
                          key=lambda f: (f.priority, f.severity))
        gates = self.store.list(project_id, "gates")
        if fmt == "json":
            return {"assessment": a.model_dump(mode="json"), "findings": [f.model_dump(mode="json") for f in findings],
                    "remediations": [g.model_dump(mode="json") for g in gates]}
        s = a.summary
        lines = [f"# Security Guardian report - {project_id}", "",
                 f"Assessment `{a.id}` completed {a.finished_at}.", "", "## Executive summary", "",
                 f"- Findings: {s.get('total', 0)} ({s.get('open', 0)} open); critical/high open: {s.get('critical_high_open', 0)}",
                 f"- Verified by a safe test (open): {s.get('verified_open', 0)}; accepted risks: {s.get('accepted_risks', 0)}",
                 f"- Fix verified: {sum(1 for f in findings if f.state == 'fix_verified')}; fixed (static re-check only): "
                 f"{sum(1 for f in findings if f.state == 'fixed')}",
                 "- No finding is \"verified\" from a rule match alone; no finding is \"fixed\" from a generated patch alone.",
                 "- An empty result does not mean the project is secure: see coverage and limitations below.", "",
                 "## Tools", ""]
        lines += [f"- {t.tool}: {t.status} - {t.detail}" + (f" (version {t.version})" if t.version else "")
                  + (f", advisories retrieved {t.retrieved_at}" if t.retrieved_at else "") for t in a.tools]
        lines += ["", "## Findings by priority", ""]
        for f in findings:
            lines += [f"### [{f.priority}] {f.title}", "",
                      f"- Severity {f.severity}, confidence {f.confidence}, state **{f.state}**, category {f.category}",
                      f"- Location: {f.file}:{f.line}" + (f" - route {f.route}" if f.route else ""),
                      f"- Detected by: {', '.join(f.detection)}; references: {', '.join(f.references) or '-'}",
                      f"- Evidence: {redact('; '.join(e.detail for e in f.evidence))[:400]}",
                      f"- Priority reasons: {'; '.join(f.priority_reasons)}",
                      f"- Remediation: {f.remediation}"]
            if f.verification and f.verification.method != "-":
                lines.append(f"- Verification ({f.verification.status}): {f.verification.method} -> {f.verification.conclusion}")
            if f.state == "accepted_risk":
                lines.append(f"- Accepted by {f.accepted_by}: {f.accepted_note}")
            lines.append("")
        lines += ["## Remediations", ""]
        lines += [f"- {g.finding_id}: {g.decision} - {'; '.join(g.reasons)}" for g in gates] or ["- none"]
        lines += ["", "## Coverage and limitations", ""] + [f"- {x}" for x in a.coverage.get("not_covered", [])]
        return redact("\n".join(lines))


global_security_guardian = SecurityGuardian()


def security_status(project_id: str) -> Dict[str, Any]:
    """
    For other modules (readiness, copilot, incidents): the project's security state from the latest
    completed Guardian assessment, with findings in their current state. Never "secure": with no
    assessment the decision is NOT_ASSESSED; BLOCK for open critical/high findings that are detected or
    verified; REVIEW_NEEDED when the only critical/high ones need a person's judgement; else NO_KNOWN_BLOCKERS.
    """
    guardian = global_security_guardian
    a = guardian.store.latest(project_id, "completed")
    if a is None:
        return {"decision": "NOT_ASSESSED", "assessment_id": None, "finished_at": None, "summary": {},
                "detail": "no Security Guardian assessment has completed for this project"}
    ids = set(a.finding_ids)
    current = [f for f in guardian.store.list(project_id, "findings") if f.id in ids]
    s = correlate.summarize(current)
    serious = [f for f in current if f.severity in ("critical", "high") and "resolved_at" not in f.context
               and f.state not in ("fix_verified", "accepted_risk", "not_reproduced")]
    blocking = sum(1 for f in serious if f.state != "requires_review")
    review = len(serious) - blocking
    unavailable = [t.tool for t in a.tools if t.status != "ran"]
    detail = (f"{s['open']} open finding(s), {blocking} critical/high, {review} critical/high needing review, "
              f"{s['verified_open']} verified by a safe test "
              f"(assessment {a.id}, {a.finished_at})" + (f"; not run: {', '.join(unavailable)}" if unavailable else ""))
    decision = "BLOCK" if blocking else "REVIEW_NEEDED" if review else "NO_KNOWN_BLOCKERS"
    return {"decision": decision, "assessment_id": a.id, "finished_at": a.finished_at,
            "summary": s, "tools_unavailable": unavailable, "detail": detail}

