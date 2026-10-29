"""
AIForge Swarm Intelligence: a mission's task graph executed by specialised agents.

  plan        Mission Controller task graph (registry.py): contract -> backend || frontend client -> review ->
              integration -> verification; validated (unknown deps, unsupported tasks, cycles)
  run         (approved) a scheduler starts every task whose dependencies completed, up to the concurrency
              limit, each with a timeout and a bounded number of attempts; state is persisted after every
              transition, so an interrupted mission resumes from its completed tasks
  agents      implementation agents work in their own copy of one frozen snapshot and may write only their
              owned paths; what they produce becomes an artifact (provenance: creator, task, base revision,
              content hash, schema validation). The code is read back (routes, client calls) - an agent's own
              description of its output is never used.
  review      the Critical Reviewer's rule findings (consensus.review)
  integrate   ownership and file conflicts, static interface matching (interfaces.match), then (v2) runtime
              contract tests: the integrated backend in the Chaos sandbox and the real generated JS client in a
              node container on the same internal network (runtime.py). Results become structured findings
              (findings.py): 'verified' only with runtime evidence and an established responsible component.
  repair      at most one automatic repair per identified mismatch, and only when exactly one component is
              demonstrably responsible: that component is asked again with the evidence and the expected
              behaviour; the new version supersedes (never overwrites) the old one; behaviour is re-extracted and
              re-tested and every mandatory gate runs again. A failed repair, both components departing, flaky or
              insufficient evidence -> a person decides (NEEDS_HUMAN_REVIEW, with an Autopilot review plan).
  verify      runtime contract tests, isolation + cleanup (inspected from Docker), project tests + a generated
              contract test, Security Guardian re-check (also after every repair); a mandatory gate that fails
              or cannot run means the mission is not successful, whatever the agents reported
  review      Autopilot output: contract / backend / frontend versions, results, repair history, unresolved
              findings, evidence and proposed actions. Success -> a write_files plan awaiting approval; failure ->
              an evidence-backed report and, where appropriate, a remediation plan. Nothing is written to the
              project and nothing is deployed by the swarm.

Lifecycle (Mission.phase): PLANNING -> CONTRACT_READY -> PARALLEL_GENERATION -> STATIC_VALIDATION ->
INTEGRATION_TESTING -> FAILURE_CLASSIFICATION -> [REPAIR_REQUIRED -> ... -> REVALIDATION] ->
SECURITY_VERIFICATION -> AUTOPILOT_REVIEW; Mission.outcome: SUCCEEDED | FAILED | BLOCKED | NEEDS_HUMAN_REVIEW
(status completed | failed | blocked | awaiting_decision).
"""

import concurrent.futures as cf
import hashlib
import json
import logging
import shutil
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from backend.evolution.autopilot.models import now_iso
from backend.evolution.autopilot.redact import redact
from backend.evolution.autopilot.store import AutopilotStore
from backend.swarm import consensus, findings, interfaces, registry
from backend.swarm.models import (Artifact, Conflict, Contract, Finding, Gate, Message, Mission, Proposal, RepairAttempt,
                                  Task)

_logger = logging.getLogger("aiforge.swarm")
DEFAULTS = {"concurrency": 2, "max_messages": 200, "max_repair_rounds": 1, "mission_seconds": 3600, "priorities": {}}
BACKEND_PROMPT = ("You are AIForge's Backend Agent. Implement exactly the API contract below in FastAPI: Pydantic "
                  "request models matching each request_schema, the contract's success status codes (status_code=) "
                  "and response bodies, its documented errors and its authentication, plus pytest tests using "
                  "fastapi.testclient for every endpoint. Return each file as '### path' and a fenced code block.")
FRONTEND_PROMPT = ("You are AIForge's Frontend Agent. Write a JavaScript ES module frontend/src/api/client.js with one "
                   "exported async function per contract endpoint, using fetch with the contract's exact method, path, "
                   "query parameters, headers (Authorization: Bearer <token from localStorage> when auth is bearer) "
                   "and JSON body, returning the parsed JSON response. Return the file as '### path' and a fenced code block.")
TERMINAL = {"completed": "SUCCEEDED", "failed": "FAILED", "blocked": "BLOCKED", "awaiting_decision": "NEEDS_HUMAN_REVIEW"}
OPEN_FINDING = ("verified", "unresolved", "repair_failed", "needs_human_review", "blocked")


class SwarmError(ValueError):
    pass


class Busy(RuntimeError):
    pass


class SwarmStore(AutopilotStore):
    KINDS = {"missions": Mission}
    PRUNE = (("missions", 50, "created_at"),)
    ENV_DIR = "AIFORGE_SWARM_DIR"
    DEFAULT_ROOT = Path(__file__).resolve().parents[1] / "data" / "swarm"

    def close_interrupted(self) -> int:
        n = 0
        if not self.root.is_dir():
            return 0
        for path in self.root.glob("*.json"):
            try:
                missions = self.list(path.stem, "missions")
            except ValueError:
                continue
            for m in missions:
                if m.status == "running":
                    def change(x: Mission):
                        for t in x.tasks:
                            if t.status in ("running", "ready"):
                                t.status, t.error = "pending", "interrupted by a restart; will run again on resume"
                        x.status, x.error = "interrupted", "the server stopped while the mission ran: resume it"
                    self.update(path.stem, "missions", m.id, change)
                    n += 1
        return n


def _hash(content: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()


def _example(t: str) -> Any:
    return {"int": 1, "float": 1.5, "bool": True, "list": [], "List": [], "dict": {}, "Dict": {}}.get(t, "example")


class SwarmEngine:
    def __init__(self, store: Optional[SwarmStore] = None, background: bool = True,
                 generate: Optional[Callable[[str, str], str]] = None, runtime: Optional[Callable[[], Any]] = None,
                 require_isolation: bool = True, autopilot=None):
        self.store = store or SwarmStore()
        self.background = background
        self.generate = generate               # None: the local coding model; tests inject fixed agent answers
        # runtime factory for the integration tests; None = the Docker runtime. Only code (tests) can change it,
        # and an engine that does not require isolation never lets an unisolated run pass the isolation gate.
        self.runtime = runtime
        self.require_isolation = require_isolation
        self.autopilot = autopilot             # None: the global Autopilot service (plans awaiting approval)
        self._active: Dict[str, str] = {}
        self._lock = threading.Lock()
        self._snapshots: Dict[str, Path] = {}
        self._base_findings: Dict[str, set] = {}       # per snapshot: the base project's findings (computed once)
        if background:
            try:
                self.store.close_interrupted()
            except Exception as e:  # noqa: BLE001
                _logger.warning("Swarm: could not close interrupted missions: %s", e)

    # --- mission lifecycle -------------------------------------------------------------------------------------

    def create(self, project_id: str, user_id: str, objective: str, contract: Optional[Contract],
               constraints: Optional[List[str]] = None, acceptance: Optional[List[str]] = None,
               settings: Optional[Dict[str, Any]] = None, tasks: Optional[List[Task]] = None) -> Mission:
        plan, errors = (tasks, registry.validate_graph(tasks)) if tasks is not None else registry.mission_plan(contract)
        m = Mission(id="swm_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id, objective=objective,
                    contract=contract, constraints=constraints or [], acceptance=acceptance or [],
                    settings={**DEFAULTS, **(settings or {})}, tasks=plan, plan_errors=errors,
                    status="rejected" if errors else "planned")
        self.store.put(project_id, "missions", m)
        self._tm(project_id, m.id, "task_created", "Mission Controller", f"mission planned: {objective[:120]}",
                 "rejected" if errors else "info", data={"tasks": [t.id + ":" + t.kind for t in plan], "errors": errors})
        return m

    def run(self, project_id: str, project: Path, user_id: str, mission_id: str, approved: bool) -> Mission:
        m = self._get(project_id, mission_id)
        if m.status not in ("planned", "interrupted", "awaiting_decision", "blocked"):
            raise SwarmError(f"the mission is '{m.status}'")
        if not approved:
            raise SwarmError("agents generate code that is run in the sandbox: approve the mission explicitly")
        if m.status == "blocked":                  # the environment is back: run the blocked tasks again
            def unblock(x: Mission):
                for t in x.tasks:
                    if t.status == "blocked":
                        t.status, t.error, t.attempts = "pending", None, 0
                x.outcome = None
            self.store.update(project_id, "missions", mission_id, unblock)
        with self._lock:
            if project_id in self._active:
                raise Busy(f"another swarm mission ({self._active[project_id]}) is running for this project")
            self._active[project_id] = mission_id
        self.store.update(project_id, "missions", mission_id, lambda x: (
            setattr(x, "status", "running"), setattr(x, "started_at", x.started_at or now_iso()), setattr(x, "error", None)))

        def go():
            try:
                self._schedule(project_id, mission_id, Path(project))
            finally:
                with self._lock:
                    self._active.pop(project_id, None)
        if self.background:
            threading.Thread(target=go, name=f"swarm-{mission_id}", daemon=True).start()
        else:
            go()
        return self._get(project_id, mission_id)

    def cancel(self, project_id: str, mission_id: str) -> Mission:
        def change(x: Mission):
            x.cancel_requested = True
            if x.status != "running":
                for t in x.tasks:
                    if t.status in ("pending", "ready", "blocked"):
                        t.status = "cancelled"
                if x.status in ("planned", "awaiting_decision", "interrupted"):
                    x.status, x.finished_at = "cancelled", now_iso()
        return self.store.update(project_id, "missions", mission_id, change)

    def decide(self, project_id: str, project: Path, user_id: str, mission_id: str, conflict_id: str, proposal_id: str) -> Mission:
        """A person's decision on an escalated conflict; the mission then resumes."""
        m = self._get(project_id, mission_id)
        c = next((x for x in m.conflicts if x.id == conflict_id), None)
        if c is None or c.status != "escalated":
            raise SwarmError("only an escalated conflict can be decided")
        p = next((x for x in c.proposals if x.id == proposal_id), None)
        if p is None:
            raise SwarmError("unknown proposal")
        if p.violates:
            raise SwarmError("that proposal violates a mandatory constraint: " + "; ".join(p.violates))

        def change(x: Mission):
            cc = next(y for y in x.conflicts if y.id == conflict_id)
            cc.status = "resolving"
            cc.decision = {**(cc.decision or {}), "by": f"user {user_id}", "selected": proposal_id, "at": now_iso()}
            open_f = [f for f in x.findings if f.status in ("verified", "repair_failed", "needs_human_review", "unresolved")]
            self._apply_resolution(x, p.action, f"decided by {user_id}: {p.title}. " + self._evidence_text(open_f),
                                   requested_by=f"user {user_id}", findings_=open_f)
            x.outcome = None
        self.store.update(project_id, "missions", mission_id, change)
        self._message(project_id, mission_id, f"user {user_id}", "propose_resolution", f"decision: {p.title}", task_id="t5")
        self._tm(project_id, mission_id, "approval_granted", f"user {user_id}", f"conflict {conflict_id}: {p.title}", "success")
        return self.run(project_id, project, user_id, mission_id, approved=True)

    def deliver(self, project_id: str, user_id: str, mission_id: str) -> Mission:
        """The integrated files as an Autopilot plan awaiting approval; nothing is written to the project here.
        A successful mission already produced it (this returns that plan)."""
        m = self._get(project_id, mission_id)
        if m.status != "completed":
            raise SwarmError("only a mission whose mandatory gates passed can be delivered")
        if m.delivery.get("autopilot_plan_id") and m.delivery.get("kind", "write_files") == "write_files":
            return m
        self._autopilot_plan(project_id, mission_id, user_id, "write_files")
        return self._get(project_id, mission_id)

    def _autopilot_service(self):
        if self.autopilot is not None:
            return self.autopilot
        from backend.evolution.autopilot.service import global_autopilot_service
        return global_autopilot_service

    def _autopilot_plan(self, project_id: str, mission_id: str, user_id: str, kind: str) -> Optional[str]:
        """kind write_files: the integrated files (success). kind review: proposed actions only (no file contents),
        for a person to review. Either way the plan awaits approval; the swarm writes nothing."""
        from backend.evolution.autopilot.models import Plan, PlanTask
        from backend.evolution.autopilot.plans import STRATEGY_AGENT
        m = self._get(project_id, mission_id)
        review = m.autopilot_review or {}
        if kind == "write_files":
            files = self._integrated_files(m)
            tasks = [PlanTask(id="t1", title="apply the integrated swarm output", finding_ids=[], files=sorted(files),
                              strategy="write_files", agent=STRATEGY_AGENT["write_files"],
                              modification=f"files from mission {mission_id} (contract {review.get('contract_version')})",
                              contents=files)]
            expected, checks = sorted(files), ["python_syntax", "quality_gate", "security_static", "tests"]
            objective = f"Swarm mission: {m.objective[:120]}"
        else:
            actions = review.get("proposed_actions") or ["review the swarm mission's evidence"]
            tasks = [PlanTask(id=f"t{i + 1}", title=a[:200], finding_ids=[], files=[], strategy="manual",
                              agent=STRATEGY_AGENT["manual"], modification=a[:1000]) for i, a in enumerate(actions[:10])]
            expected, checks = [], []
            objective = f"Swarm mission needs review ({m.outcome}): {m.objective[:100]}"
        plan = Plan(id="pln_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id, objective=objective, finding_ids=[],
                    tasks=tasks, expected_files=expected, agents=sorted({t.agent for t in m.tasks if t.agent}), checks=checks,
                    risks=["generated code: review the diff before approving"] if kind == "write_files" else
                    ["unresolved integration findings; see the mission's evidence"],
                    assumptions=[f"verified in an isolated workspace by mission {mission_id}" if kind == "write_files" else
                                 f"evidence: mission {mission_id} findings and runtime runs {review.get('evidence_refs', {}).get('runtime_runs')}"],
                    approval_required=["apply the swarm's integrated files"] if kind == "write_files" else ["a person decides the next step"],
                    completion_criteria=["the project's tests pass with the files applied"] if kind == "write_files" else
                    ["every unresolved finding is decided"], origin="swarm", origin_ref=mission_id)
        self._autopilot_service().store.put(project_id, "plans", plan)

        def change(x: Mission):
            x.delivery = {"autopilot_plan_id": plan.id, "kind": kind, "files": expected,
                          "status": "awaiting approval in Autopilot"}
            x.autopilot_review = {**x.autopilot_review, "approval_status": f"awaiting approval in Autopilot (plan {plan.id})",
                                  "autopilot_plan_id": plan.id}
        self.store.update(project_id, "missions", mission_id, change)
        self._tm(project_id, mission_id, "approval_requested", "Swarm Intelligence",
                 f"{'delivery' if kind == 'write_files' else 'review'} plan {plan.id} awaiting approval ({len(expected)} files)", "info")
        return plan.id

    def active(self, project_id: str) -> Optional[str]:
        with self._lock:
            return self._active.get(project_id)

    # --- helpers -------------------------------------------------------------------------------------------------

    def _get(self, project_id: str, mission_id: str) -> Mission:
        m = self.store.get(project_id, "missions", mission_id)
        if m is None:
            raise KeyError(mission_id)
        return m

    def _phase(self, project_id: str, mission_id: str, phase: str, note: str = "") -> None:
        def change(x: Mission):
            if x.phase != phase:
                x.phase = phase
                x.phase_history.append({"phase": phase, "at": now_iso(), "note": note[:300]})
        self.store.update(project_id, "missions", mission_id, change)

    def _tm(self, project_id, mission_id, type, source, summary, outcome="info", data=None) -> None:
        from backend.time_machine.recorder import emit
        emit(project_id, type, source, summary, outcome, task_id=mission_id, refs={"mission_id": mission_id},
             parent_ref=("mission_id", mission_id), data=data or {})

    def _message(self, project_id: str, mission_id: str, sender: str, type: str, summary: str, task_id: Optional[str] = None,
                 recipient: str = "swarm", artifact_refs=None, evidence_refs=None, proposed_action=None, confidence=None) -> None:
        msg = Message(id="msg_" + uuid.uuid4().hex[:10], sender=sender, recipient=recipient, task_id=task_id, type=type,
                      summary=redact(summary, 600), artifact_refs=artifact_refs or [], evidence_refs=evidence_refs or [],
                      proposed_action=proposed_action, confidence=confidence)

        def add(x: Mission):
            if len(x.messages) >= x.settings.get("max_messages", 200):
                x.cancel_requested = True
                x.error = f"message limit ({x.settings.get('max_messages')}) reached: the mission was stopped"
                return
            x.messages.append(msg)
        self.store.update(project_id, "missions", mission_id, add)

    def _artifact(self, project_id: str, mission_id: str, task: Task, agent: str, kind: str, content: Dict[str, Any],
                  revision: Optional[str]) -> Artifact:
        errors = self._validate(kind, content)
        previous = next((a for a in reversed(self._get(project_id, mission_id).artifacts)
                         if a.task_id == task.id and a.kind == kind), None)
        a = Artifact(id="art_" + uuid.uuid4().hex[:10], kind=kind, creator=agent, task_id=task.id, revision=revision,
                     content=content, content_hash=_hash(content), validation="invalid" if errors else "valid",
                     validation_errors=errors, supersedes=previous.id if previous else None)

        def add(x: Mission):
            x.artifacts.append(a)
            t = next(y for y in x.tasks if y.id == task.id)
            t.artifacts.append(a.id)
        self.store.update(project_id, "missions", mission_id, add)
        self._message(project_id, mission_id, agent, "submit_artifact", f"{kind} ({'valid' if not errors else 'invalid'})",
                      task_id=task.id, artifact_refs=[a.id])
        return a

    @staticmethod
    def _validate(kind: str, c: Dict[str, Any]) -> List[str]:
        errors = []
        if kind == "contract":
            seen = set()
            for e in c.get("endpoints", []):
                if e.get("method", "").upper() not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                    errors.append(f"invalid method {e.get('method')}")
                if not str(e.get("path", "")).startswith("/"):
                    errors.append(f"path must start with /: {e.get('path')}")
                k = (e.get("method", "").upper(), interfaces._norm(str(e.get("path", ""))))
                if k in seen:
                    errors.append(f"duplicate operation {k}")
                seen.add(k)
                for status in list((e.get("responses") or {})) + list((e.get("errors") or {})):
                    if not (str(status).isdigit() and 100 <= int(status) <= 599):
                        errors.append(f"{k}: invalid status code {status!r}")
                if not any(str(x).startswith("2") for x in (e.get("responses") or {})):
                    errors.append(f"{k}: no success response")
                for name, sch in [("request_schema", e.get("request_schema"))] + [
                        (f"response {st}", (r or {}).get("schema")) for st, r in (e.get("responses") or {}).items()]:
                    if sch is not None:
                        try:
                            import jsonschema
                            jsonschema.Draft202012Validator.check_schema(sch)
                        except Exception as ex:  # noqa: BLE001
                            errors.append(f"{k}: {name} is not a valid JSON Schema: {str(ex).splitlines()[0][:120]}")
            if not c.get("endpoints"):
                errors.append("no endpoints")
        elif kind == "source_files":
            files = c.get("files", {})
            if not files or not all(isinstance(k, str) and isinstance(v, str) for k, v in files.items()):
                errors.append("no files, or a file is not text")
            owned = c.get("owned_paths", [])
            outside = [k for k in files if not any(k.startswith(o) for o in owned)]
            if outside:
                errors.append(f"files outside the task's owned paths: {outside}")
        elif kind in ("route_inventory", "client_calls"):
            if not isinstance(c.get("items"), list):
                errors.append("items must be a list")
        return errors

    def _latest(self, m: Mission, task_id: str, kind: str) -> Optional[Artifact]:
        return next((a for a in reversed(m.artifacts) if a.task_id == task_id and a.kind == kind and a.validation == "valid"), None)

    def _snapshot(self, project_id: str, mission_id: str, project: Path) -> Path:
        from backend.evolution.autopilot.workspace import create_workspace
        from backend.evolution_engine.service import source_revision
        if mission_id not in self._snapshots or not self._snapshots[mission_id].exists():
            snap = create_workspace(project, prefix="aiforge_swarm_base_")
            self._snapshots[mission_id] = snap
            rev = source_revision(snap)
            m = self._get(project_id, mission_id)
            if m.base_revision and m.base_revision != rev:
                raise SwarmError("the project changed since this mission started; create a new mission")
            self.store.update(project_id, "missions", mission_id, lambda x: setattr(x, "base_revision", rev))
        return self._snapshots[mission_id]

    # --- the scheduler ---------------------------------------------------------------------------------------------

    def _schedule(self, project_id: str, mission_id: str, project: Path) -> None:
        m = self._get(project_id, mission_id)
        deadline = time.monotonic() + m.settings.get("mission_seconds", 3600)
        pool = cf.ThreadPoolExecutor(max_workers=max(1, int(m.settings.get("concurrency", 2))), thread_name_prefix="swarm")
        running: Dict[str, Any] = {}
        try:
            snapshot = self._snapshot(project_id, mission_id, project)
            while True:
                m = self._get(project_id, mission_id)
                if m.cancel_requested or time.monotonic() > deadline:
                    why = m.error or ("cancelled by the user" if m.cancel_requested else "the mission's time limit was reached")
                    self._finish(project_id, mission_id, "cancelled" if "user" in why else "failed", why, running)
                    return
                if m.status == "awaiting_decision":
                    # the task that escalated may still be writing the report and the Autopilot review plan:
                    # let in-flight tasks finish before handing the mission to a person
                    for tid, (fut, started, t) in list(running.items()):
                        try:
                            fut.result(timeout=max(1.0, t.timeout_seconds - (time.monotonic() - started)))
                        except Exception:  # noqa: BLE001 - recorded by _complete / _failed below
                            pass
                        running.pop(tid)
                        if fut.done():
                            self._complete(project_id, mission_id, t, fut)
                        else:
                            self._failed(project_id, mission_id, t, f"timed out after {t.timeout_seconds}s")
                    return                                   # resumes when a person decides
                done = {t.id for t in m.tasks if t.status == "completed"}
                bad = {t.id for t in m.tasks if t.status in ("failed", "cancelled", "blocked")}
                changed = False
                for t in m.tasks:
                    if t.status == "pending" and any(d in bad for d in t.depends_on):
                        self._set(project_id, mission_id, t.id, status="blocked",
                                  error="a task it depends on did not complete: " + ", ".join(d for d in t.depends_on if d in bad))
                        changed = True
                    elif t.status == "pending" and all(d in done for d in t.depends_on) and t.id not in running \
                            and len(running) < int(m.settings.get("concurrency", 2)):
                        self._set(project_id, mission_id, t.id, status="running", started_at=now_iso(), attempts=t.attempts + 1)
                        self._tm(project_id, mission_id, "agent_started", t.agent or "?", f"{t.id}: {t.objective}")
                        running[t.id] = (pool.submit(self._execute, project_id, mission_id, t.id, project, snapshot), time.monotonic(), t)
                        changed = True
                for tid, (fut, started, t) in list(running.items()):
                    if fut.done():
                        running.pop(tid)
                        self._complete(project_id, mission_id, t, fut)
                        changed = True
                    elif time.monotonic() - started > t.timeout_seconds:
                        running.pop(tid)                     # the thread cannot be killed; its result is ignored
                        self._failed(project_id, mission_id, t, f"timed out after {t.timeout_seconds}s")
                        changed = True
                m = self._get(project_id, mission_id)
                if not running and all(t.status in ("completed", "failed", "cancelled", "blocked") for t in m.tasks):
                    self._conclude(project_id, mission_id)
                    return
                if not running and not changed and m.status != "awaiting_decision" \
                        and not any(t.status == "pending" for t in m.tasks):
                    self._conclude(project_id, mission_id)
                    return
                if not changed:
                    time.sleep(0.2)
        except Exception as e:  # noqa: BLE001
            _logger.exception("Swarm mission %s failed", mission_id)
            self._finish(project_id, mission_id, "failed", redact(f"{type(e).__name__}: {e}", 800), running)
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
            m = self.store.get(project_id, "missions", mission_id)
            if m and m.status != "awaiting_decision":
                snap = self._snapshots.pop(mission_id, None)
                if snap:
                    self._base_findings.pop(str(snap), None)
                    shutil.rmtree(snap.parent, ignore_errors=True)

    def _set(self, project_id, mission_id, task_id, **fields) -> None:
        def change(x: Mission):
            t = next(y for y in x.tasks if y.id == task_id)
            for k, v in fields.items():
                setattr(t, k, v)
        self.store.update(project_id, "missions", mission_id, change)

    def _complete(self, project_id, mission_id, t: Task, fut) -> None:
        try:
            outcome = fut.result()
        except Exception as e:  # noqa: BLE001
            outcome = {"status": "failed", "error": redact(f"{type(e).__name__}: {e}", 600)}
        status = outcome.get("status", "failed")
        if status == "failed":
            self._failed(project_id, mission_id, t, outcome.get("error") or "failed")
            return
        if status == "requeued":
            return                                           # a repair round put tasks back to pending
        self._set(project_id, mission_id, t.id, status=status, finished_at=now_iso(), error=outcome.get("error"))
        self._tm(project_id, mission_id, "agent_completed", t.agent or "?", f"{t.id}: {status}",
                 "success" if status == "completed" else "info")

    def _failed(self, project_id, mission_id, t: Task, error: str) -> None:
        cur = next(x for x in self._get(project_id, mission_id).tasks if x.id == t.id)
        if cur.attempts <= cur.retry_limit:
            self._set(project_id, mission_id, t.id, status="pending", error=f"attempt {cur.attempts} failed: {error}")
            self._message(project_id, mission_id, t.agent or "?", "report_failure", f"{t.id} attempt {cur.attempts}: {error}; retrying",
                          task_id=t.id)
        else:
            self._set(project_id, mission_id, t.id, status="failed", finished_at=now_iso(), error=error)
            self._message(project_id, mission_id, t.agent or "?", "report_failure", f"{t.id} failed: {error}", task_id=t.id)
            self._tm(project_id, mission_id, "agent_completed", t.agent or "?", f"{t.id} failed: {error}", "failure")

    def _finish(self, project_id, mission_id, status, error, running) -> None:
        def change(x: Mission):
            for t in x.tasks:
                if t.status in ("pending", "ready", "running", "blocked"):
                    t.status = "cancelled"
            x.status, x.error, x.finished_at = status, error, now_iso()
            x.outcome = None if status == "cancelled" else "FAILED"
        self.store.update(project_id, "missions", mission_id, change)
        self._report(project_id, mission_id)

    def _conclude(self, project_id, mission_id) -> None:
        m = self._get(project_id, mission_id)
        self._phase(project_id, mission_id, "AUTOPILOT_REVIEW", "every task has finished")
        mandatory = [g for g in m.gates if g.mandatory]
        open_findings = [f for f in self._current_findings(m) if f.status in OPEN_FINDING]
        ok = all(t.status == "completed" for t in m.tasks) and mandatory and all(g.status == "passed" for g in mandatory)
        open_conflicts = [c for c in m.conflicts if c.status in ("open", "escalated")]
        infra = any(f.status == "blocked" for f in open_findings) or any(g.status == "unavailable" for g in mandatory)
        failed_gate = any(g.status in ("failed", "flaky") for g in mandatory)
        if ok and not open_conflicts and not open_findings:
            status = "completed"
        elif infra and not failed_gate and not any(f.status in ("verified", "repair_failed") for f in open_findings):
            status = "blocked"
        else:
            status = "failed"
        why = None if status == "completed" else (
            "the isolated environment or a mandatory check was unavailable" if status == "blocked" else
            "unresolved conflicts" if open_conflicts else
            "a mandatory gate did not pass" if mandatory and not all(g.status == "passed" for g in mandatory) else
            "integration findings remain" if open_findings else
            "not every task completed")
        self.store.update(project_id, "missions", mission_id, lambda x: (
            setattr(x, "status", status), setattr(x, "error", why), setattr(x, "finished_at", now_iso()),
            setattr(x, "outcome", TERMINAL[status])))
        self._report(project_id, mission_id)
        self._review(project_id, mission_id)
        self._tm(project_id, mission_id, "task_completed" if status == "completed" else "task_failed", "Swarm Intelligence",
                 f"mission {TERMINAL[status]}" + (f": {why}" if why else ""), "success" if status == "completed" else "failure")

    @staticmethod
    def _current_findings(m: Mission) -> List[Finding]:
        """Findings of the latest integration round (earlier rounds are history), plus security findings."""
        latest = max((f.round for f in m.findings if f.basis != "security"), default=0)
        return [f for f in m.findings if f.round == latest or f.basis == "security"]

    def _review(self, project_id: str, mission_id: str) -> None:
        """Phase 7: the Autopilot output, and the plan that awaits approval (write_files on success; proposed
        actions only for a person otherwise). Never claims the project was modified or deployed."""
        m = self._get(project_id, mission_id)
        latest = lambda tid: self._latest(m, tid, "source_files")  # noqa: E731
        version = lambda a, tid: ({"artifact": a.id, "content_hash": a.content_hash[:16], "creator": a.creator,  # noqa: E731
                                   "version": sum(1 for x in m.artifacts if x.task_id == tid and x.kind == "source_files"),
                                   "supersedes": a.supersedes} if a else None)
        run = m.runtime[-1] if m.runtime else {}
        gates = {g.name: {"status": g.status, "detail": g.detail} for g in m.gates}
        unresolved = [f for f in self._current_findings(m) if f.status in OPEN_FINDING]
        actions: List[str] = []
        for f in unresolved:
            who = f.responsible or "a person (responsibility not established)"
            actions.append(f"[{f.category}] {f.endpoint}: {f.recommended_correction} - responsible: {who}; "
                           f"expected {f.expected}; observed {f.observed[:200]}")
        for g in m.gates:
            if g.mandatory and g.status != "passed":
                actions.append(f"gate '{g.name}' is {g.status}: {g.detail[:200]}")
        if m.outcome == "BLOCKED":
            actions.append("make the isolated Docker environment available, then resume the mission (nothing was executed)")
        review = {
            "objective": m.objective, "outcome": m.outcome, "status": m.status,
            "contract_version": m.contract.revision() if m.contract else None,
            "contract_format": m.contract.version if m.contract else None,
            "backend_version": version(latest("t2"), "t2"), "frontend_version": version(latest("t3"), "t3"),
            "contract_validation": {"artifact": next((a.id for a in m.artifacts if a.kind == "contract"), None),
                                    "valid": next((a.validation for a in m.artifacts if a.kind == "contract"), None),
                                    "static_findings": [f"{f.endpoint}: {f.observed}" for f in self._current_findings(m) if f.basis == "static"][:20]},
            "generated_tests": gates.get("project and contract tests"),
            "integration_tests": {"run": run.get("id"), "status": run.get("status"), "environment": run.get("environment"),
                                  "counts": run.get("counts"), "rerun": run.get("rerun", False),
                                  "gate": gates.get("runtime contract tests")},
            "security": gates.get("security (no new critical/high)"), "isolation": gates.get("isolation and cleanup"),
            "repair_history": [r.model_dump() for r in m.repairs],
            "unresolved_findings": [{"id": f.id, "category": f.category, "endpoint": f.endpoint, "status": f.status,
                                     "responsible": f.responsible, "observed": f.observed[:300]} for f in unresolved],
            "evidence_refs": {"runtime_runs": [r.get("id") for r in m.runtime], "artifacts": [a.id for a in m.artifacts],
                              "findings": [f.id for f in m.findings]},
            "proposed_actions": actions or ["approve the Autopilot plan to apply the integrated files"],
            "approval_status": "no plan (blocked: nothing to approve)" if m.outcome == "BLOCKED" else "pending",
            "project_modified": False, "deployed": False,
        }
        self.store.update(project_id, "missions", mission_id, lambda x: setattr(x, "autopilot_review", review))
        try:
            if m.outcome == "SUCCEEDED":
                self._autopilot_plan(project_id, mission_id, m.user_id, "write_files")
            elif m.outcome in ("NEEDS_HUMAN_REVIEW", "FAILED") and unresolved:
                self._autopilot_plan(project_id, mission_id, m.user_id, "review")
        except Exception as e:  # noqa: BLE001
            _logger.warning("Swarm: could not create the Autopilot plan: %s", e)
            note = f"the Autopilot plan could not be created: {type(e).__name__}"
            self.store.update(project_id, "missions", mission_id, lambda x: x.autopilot_review.update({"approval_status": note}))

    def _report(self, project_id, mission_id) -> None:
        m = self._get(project_id, mission_id)
        current = self._current_findings(m)
        rep = {
            "status": m.status, "outcome": m.outcome, "phase": m.phase, "error": m.error,
            "completed_tasks": [t.id + " " + t.objective for t in m.tasks if t.status == "completed"],
            "failed_tasks": [f"{t.id} {t.objective}: {t.error}" for t in m.tasks if t.status in ("failed", "blocked", "cancelled")],
            "unresolved_conflicts": [c.detail for c in m.conflicts if c.status in ("open", "escalated")],
            "resolved_conflicts": [{"detail": c.detail, "decision": c.decision} for c in m.conflicts if c.status == "resolved"],
            "gates": [g.model_dump() for g in m.gates],
            "findings": {"open": [f.id for f in current if f.status in OPEN_FINDING],
                         "repaired": [f.id for f in m.findings if f.status == "repaired"],
                         "by_category": {c: sum(1 for f in current if f.category == c) for c in sorted({f.category for f in current})}},
            "repairs": [{"id": r.id, "component": r.component, "outcome": r.outcome, "requested_by": r.requested_by} for r in m.repairs],
            "runtime_runs": [{"id": r.get("id"), "round": r.get("round"), "status": r.get("status"), "counts": r.get("counts")} for r in m.runtime],
            "artifacts": [{"id": a.id, "kind": a.kind, "creator": a.creator, "task": a.task_id, "validation": a.validation}
                          for a in m.artifacts],
            "messages": len(m.messages),
            "limitations": ["values for client calls come from the contract (and the backend's declared types where the contract "
                            "leaves a type open); business logic beyond the contract is not judged",
                            "operations that require authentication can only be verified as far as a dummy credential allows",
                            "Performance and Chaos gates are not selected for API-contract missions",
                            "agents' stated confidence is not used as evidence"],
        }
        self.store.update(project_id, "missions", mission_id, lambda x: setattr(x, "report", rep))

    # --- task execution ----------------------------------------------------------------------------------------------

    def _execute(self, project_id: str, mission_id: str, task_id: str, project: Path, snapshot: Path) -> Dict[str, Any]:
        m = self._get(project_id, mission_id)
        t = next(x for x in m.tasks if x.id == task_id)
        handler = {"contract": self._do_contract, "backend": self._do_agent, "frontend_client": self._do_agent,
                   "review": self._do_review, "integration": self._do_integration, "verification": self._do_verification}[t.kind]
        phase = {"backend": "REPAIR_REQUIRED" if t.feedback else "PARALLEL_GENERATION",
                 "frontend_client": "REPAIR_REQUIRED" if t.feedback else "PARALLEL_GENERATION",
                 "review": "STATIC_VALIDATION", "integration": "STATIC_VALIDATION", "verification": "SECURITY_VERIFICATION"}.get(t.kind)
        if phase:
            self._phase(project_id, mission_id, phase, f"{t.id} {t.objective}")
        out = handler(project_id, mission_id, t, snapshot)
        if t.kind == "contract" and out.get("status") == "completed":
            self._phase(project_id, mission_id, "CONTRACT_READY", "the contract is valid")
        return out

    def _do_contract(self, project_id, mission_id, t: Task, snapshot: Path) -> Dict[str, Any]:
        m = self._get(project_id, mission_id)
        a = self._artifact(project_id, mission_id, t, t.agent, "contract", m.contract.model_dump() if m.contract else {}, m.base_revision)
        if a.validation != "valid":
            return {"status": "failed", "error": "invalid contract: " + "; ".join(a.validation_errors)}
        self.store.update(project_id, "missions", mission_id, lambda x: setattr(next(y for y in x.artifacts if y.id == a.id), "approved", True))
        return {"status": "completed"}

    def _do_agent(self, project_id, mission_id, t: Task, snapshot: Path) -> Dict[str, Any]:
        from backend.evolution.autopilot.executor import HiddenLineChanged, model_changes
        from backend.evolution.autopilot.workspace import create_workspace, discard_workspace
        m = self._get(project_id, mission_id)
        contract = json.dumps(m.contract.model_dump(), indent=1)
        ws = create_workspace(snapshot, prefix=f"aiforge_swarm_{t.id}_")
        try:
            prompt = BACKEND_PROMPT if t.kind == "backend" else FRONTEND_PROMPT
            request = (f"Agent: {t.agent}\nMission: {m.objective}\nConstraints: {'; '.join(m.constraints) or 'none'}\n"
                       f"API contract (JSON):\n{contract}\nTask: {t.objective}")
            changes, feedback = {}, t.feedback or ""
            for _ in range(2):
                try:
                    changes = model_changes(ws, project_id, t.owned_paths, [], request, self.generate, feedback,
                                            topic=t.objective, system_prompt=prompt)
                except HiddenLineChanged as e:
                    feedback = str(e)
                    continue
                outside = [p for p in changes if not any(p.startswith(o) for o in t.owned_paths)]
                if outside:
                    feedback = f"you may only write {t.owned_paths}; you wrote {outside}"
                    changes = {}
                    continue
                if changes:
                    break
                feedback = feedback or "no file was produced"
            changes = {p: c for p, c in changes.items() if c is not None}
            if not changes:
                return {"status": "failed", "error": f"the agent produced no usable files ({feedback})"}
            for rel, content in changes.items():
                target = (ws / rel).resolve()
                if ws.resolve() not in target.parents:
                    return {"status": "failed", "error": f"unsafe path {rel}"}
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8", newline="")
            src = self._artifact(project_id, mission_id, t, t.agent, "source_files",
                                 {"files": changes, "owned_paths": t.owned_paths}, m.base_revision)
            if src.validation != "valid":
                return {"status": "failed", "error": "; ".join(src.validation_errors)}
            files = {p.relative_to(ws).as_posix(): p.read_text(encoding="utf-8", errors="replace")
                     for p in ws.rglob("*") if p.is_file() and p.suffix in (".py", ".js", ".jsx", ".ts", ".tsx", ".mjs")}
            if t.kind == "backend":
                self._artifact(project_id, mission_id, t, t.agent, "route_inventory",
                               {"items": interfaces.routes({k: v for k, v in files.items() if k.endswith(".py")}),
                                "method": "read from the code (AST)"}, m.base_revision)
            else:
                self._artifact(project_id, mission_id, t, t.agent, "client_calls",
                               {"items": interfaces.client_calls({k: v for k, v in changes.items()}),
                                "method": "read from the code (fetch calls)"}, m.base_revision)
            return {"status": "completed"}
        finally:
            discard_workspace(ws)

    def _security_new(self, project_id: str, snapshot: Path, files: Dict[str, str]) -> List[str]:
        """New critical/high Security Guardian findings in the given files, compared with the snapshot."""
        from backend.evolution.autopilot.workspace import create_workspace, discard_workspace
        from backend.guardian.service import analyze
        key = str(snapshot)
        if key not in self._base_findings:
            self._base_findings[key] = {f"{x.rule_id}|{x.file}" for x in analyze(project_id, snapshot, dependency_audit=False)[0]}
        base = self._base_findings[key]
        ws = create_workspace(snapshot, prefix="aiforge_swarm_sec_")
        try:
            for rel, c in files.items():
                (ws / rel).parent.mkdir(parents=True, exist_ok=True)
                (ws / rel).write_text(c, encoding="utf-8", newline="")
            return [f"{x.title} ({x.file}:{x.line})" for x in analyze(project_id, ws, dependency_audit=False)[0]
                    if f"{x.rule_id}|{x.file}" not in base and x.severity in ("critical", "high") and x.file in files]
        finally:
            discard_workspace(ws)

    def _do_review(self, project_id, mission_id, t: Task, snapshot: Path) -> Dict[str, Any]:
        m = self._get(project_id, mission_id)
        routes_a, calls_a, be_src = self._latest(m, "t2", "route_inventory"), self._latest(m, "t3", "client_calls"), self._latest(m, "t2", "source_files")
        contract = [e.model_dump() for e in m.contract.endpoints]
        try:
            sec = self._security_new(project_id, snapshot, be_src.content["files"]) if be_src else []
        except Exception as e:  # noqa: BLE001
            sec = []
            self._message(project_id, mission_id, t.agent, "report_failure", f"security analysis unavailable: {type(e).__name__}", task_id=t.id)
        ids = {"contract": next((a.id for a in m.artifacts if a.kind == "contract"), ""),
               "route_inventory": routes_a.id if routes_a else "", "client_calls": calls_a.id if calls_a else "",
               "source_files": be_src.id if be_src else ""}
        findings = consensus.review(contract, routes_a.content["items"] if routes_a else [],
                                    calls_a.content["items"] if calls_a else [], be_src.content["files"] if be_src else {}, sec, ids)
        self._artifact(project_id, mission_id, t, t.agent, "review", {"findings": findings, "security_new": sec}, m.base_revision)
        for f in findings:
            if f["severity"] in ("critical", "high"):
                self._message(project_id, mission_id, t.agent, "report_finding", f["detail"], task_id=t.id,
                              evidence_refs=f["based_on"], confidence="high")
        self._tm(project_id, mission_id, "review_completed", "Critical Reviewer", f"{len(findings)} finding(s)",
                 "failure" if any(f["severity"] in ("critical", "high") for f in findings) else "success",
                 data={"findings": findings[:30]})
        return {"status": "completed"}

    # --- integration and conflicts --------------------------------------------------------------------------------------

    def _integrated_files(self, m: Mission) -> Dict[str, str]:
        files: Dict[str, str] = {}
        for tid in ("t2", "t3"):
            a = self._latest(m, tid, "source_files")
            if a:
                files.update(a.content["files"])
        return files

    def _apply_resolution(self, x: Mission, action: str, why: str, requested_by: str = "integration_agent",
                          findings_: Optional[List[Finding]] = None) -> None:
        """Requeue the side(s) that must change, with the evidence as the repair request, then review, integration
        and verification run again. Each requeued side gets a RepairAttempt record."""
        side = action.split(":", 1)[1] if action.startswith("repair:") else None
        sides = ["backend", "frontend"] if side == "both" else [side]
        tids = {"frontend": "t3", "backend": "t2"}
        if not all(s in tids for s in sides):
            return
        rounds = x.settings.get("_repair_rounds", 0) + 1
        x.settings["_repair_rounds"] = rounds
        for sd in sides:
            mine = [f for f in (findings_ or []) if f.responsible == sd] or [f for f in (findings_ or []) if f.responsible is None]
            before = next((a.id for a in reversed(x.artifacts) if a.task_id == tids[sd] and a.kind == "source_files"
                           and a.validation == "valid"), None)
            rid = "rp_" + uuid.uuid4().hex[:10]
            x.repairs.append(RepairAttempt(id=rid, component=sd, task_id=tids[sd], finding_keys=sorted({f.key for f in mine}),
                                           finding_ids=[f.id for f in mine], requested_by=requested_by,
                                           request=redact(why, 4000), artifact_before=before))
            for f in x.findings:
                if f.id in {g.id for g in mine}:
                    f.repair_attempt = rid
        for t in x.tasks:
            if t.id in {tids[sd] for sd in sides}:
                t.status, t.feedback, t.attempts = "pending", why, 0
            elif t.id in ("t4", "t5", "t6"):
                t.status, t.error = "pending", None

    @staticmethod
    def _evidence_text(fs: List[Finding]) -> str:
        lines = [f"- [{f.category}] {f.endpoint}: expected {f.expected}; observed {f.observed[:300]}"
                 + (f" (evidence: check {f.evidence.get('check')}, run {f.evidence.get('runtime_run')})" if f.evidence.get("check") else "")
                 for f in fs[:12]]
        return "Evidence from the runtime contract tests:\n" + "\n".join(lines) if lines else ""

    def _do_integration(self, project_id, mission_id, t: Task, snapshot: Path) -> Dict[str, Any]:
        m = self._get(project_id, mission_id)
        be, fe = self._latest(m, "t2", "source_files"), self._latest(m, "t3", "source_files")
        routes_a, calls_a = self._latest(m, "t2", "route_inventory"), self._latest(m, "t3", "client_calls")
        conflicts: List[Conflict] = []
        # 1. ownership and file conflicts
        owners: Dict[str, str] = {}
        for a in (be, fe):
            if a is None:
                continue
            for p in a.content["files"]:
                if p in owners and owners[p] != a.task_id:
                    conflicts.append(Conflict(id="cf_" + uuid.uuid4().hex[:8], kind="file_ownership", severity="critical",
                                              components=[owners[p], a.task_id], detail=f"{p} is written by {owners[p]} and {a.task_id}"))
                owners[p] = a.task_id
        routes, calls = (routes_a.content["items"] if routes_a else []), (calls_a.content["items"] if calls_a else [])
        matched = interfaces.match(calls, routes)
        contract_v1 = [e.model_dump() for e in m.contract.endpoints]
        be_dev, fe_dev = interfaces.sides(contract_v1, routes, calls)
        report = {"calls": matched, "routes": routes, "backend_deviations": be_dev, "client_deviations": fe_dev,
                  "file_owners": owners}
        if any(c.kind == "file_ownership" for c in conflicts):
            self._save_integration(project_id, mission_id, t, conflicts, report)
            return {"status": "failed", "error": "file ownership conflicts: " + "; ".join(c.detail for c in conflicts)}
        # 2. static validation (unverified until a runtime check confirms it)
        contract = m.contract.model_dump()
        round_no = len(m.runtime) + 1
        arts = {"backend_artifact": be.id if be else None, "frontend_artifact": fe.id if fe else None,
                "route_inventory": routes_a.id if routes_a else None, "client_calls": calls_a.id if calls_a else None}
        static = findings.from_static(mission_id, round_no, contract, routes, matched, arts)
        self._record_repair_results(project_id, mission_id, be, fe)
        # 3. runtime contract tests in the isolated environment
        self._phase(project_id, mission_id, "REVALIDATION" if m.repairs else "INTEGRATION_TESTING", f"round {round_no}")
        run = self._runtime_run(project_id, mission_id, snapshot, contract, routes, fe, round_no, arts)
        # 4. classification
        self._phase(project_id, mission_id, "FAILURE_CLASSIFICATION", f"round {round_no}: {run.get('status')} {run.get('counts')}")
        observed = findings.from_runtime(mission_id, round_no, run, arts)
        declared = findings.from_declared(mission_id, round_no, contract, run.get("declared") or {}, run.get("id"))
        props = findings.properties(contract, routes, run.get("declared") or {}, run.get("checks") or [])
        report.update({"runtime_run": run.get("id"), "runtime_status": run.get("status"), "runtime_counts": run.get("counts"),
                       "findings": [f.id for f in static + declared + observed]})

        def record(x: Mission):
            x.findings.extend(static + declared + observed)
            x.properties = props
            now_keys = {f.key for f in observed}
            for f in x.findings:                    # earlier rounds' runtime findings that no longer occur
                if f.round < round_no and f.basis == "runtime" and f.status in ("verified", "unresolved") and f.key not in now_keys:
                    f.status = "repaired" if f.repair_attempt else "resolved_by_rerun"
            for r in x.repairs:
                if r.outcome == "pending" and r.artifact_after:
                    still = sorted(set(r.finding_keys) & now_keys)
                    r.validation = {**r.validation, "runtime_run": run.get("id"), "runtime_status": run.get("status"),
                                    "runtime_counts": run.get("counts"), "mismatches_remaining": still}
                    if run.get("status") == "completed":
                        r.outcome = "failed" if still else "succeeded"
                        r.completed_at = r.completed_at or now_iso()
        self.store.update(project_id, "missions", mission_id, record)
        for f in observed:
            if f.status == "verified" and f.severity in ("critical", "high"):
                self._message(project_id, mission_id, t.agent, "report_finding", f"{f.endpoint}: {f.observed}", task_id=t.id,
                              evidence_refs=[x for x in (run.get("id"), f.evidence.get("check")) if x], confidence=f.confidence)
        blocked = [f for f in observed if f.status == "blocked"]
        verified = [f for f in observed if f.status == "verified"]
        unresolved = [f for f in observed if f.status == "unresolved"]
        if blocked:
            self._save_integration(project_id, mission_id, t, conflicts, report)
            self._tm(project_id, mission_id, "test_executed", "Integration Agent", f"integration tests blocked: {blocked[0].observed[:200]}",
                     "inconclusive", data={"run": run.get("id")})
            return {"status": "blocked", "error": f"integration tests could not run: {blocked[0].observed[:300]}"}
        self._tm(project_id, mission_id, "test_executed", "Integration Agent",
                 f"round {round_no}: {run.get('counts')} ({run.get('environment')})", "success" if not verified and not unresolved else "failure",
                 data={"run": run.get("id"), "findings": [f.key for f in observed]})
        if not verified and not unresolved:
            self.store.update(project_id, "missions", mission_id, lambda x: [
                (setattr(c, "status", "resolved"), setattr(c, "decision", {**(c.decision or {}), "verified": f"runtime run {run.get('id')}: every contract check passed"}))
                for c in x.conflicts if c.kind == "api_contract" and c.status in ("resolving", "escalated")])
            self._save_integration(project_id, mission_id, t, conflicts, report)
            return {"status": "completed"}
        # 5. who must change? (evidence, never agent agreement)
        responsible = sorted({f.responsible for f in verified})
        be_v = [f"{f.endpoint}: {f.observed}" for f in verified if f.responsible == "backend"]
        fe_v = [f"{f.endpoint}: {f.observed}" for f in verified if f.responsible == "frontend"]
        detail = "; ".join(f"{f.endpoint}: {f.observed}" for f in verified + unresolved)[:3000]
        conflict = Conflict(id="cf_" + uuid.uuid4().hex[:8], kind="api_contract", severity="high",
                            components=["t2 backend", "t3 frontend client"], detail=detail,
                            evidence={"runtime_run": run.get("id"), "findings": [f.id for f in verified + unresolved],
                                      "backend_deviations": be_v, "client_deviations": fe_v, **{k: v for k, v in arts.items() if v}})
        conflict.proposals = self._proposals(be_v, fe_v, verified, routes, calls)
        attempted = {k for r in m.repairs if r.requested_by == "integration_agent" for k in r.finding_keys}
        repeat = sorted({f.key for f in verified} & attempted)
        rounds = m.settings.get("_repair_rounds", 0)
        why = None
        if len(responsible) > 1:
            why = "both components depart from the contract: a person decides which to change"
        elif unresolved and not verified:
            why = "the evidence does not establish which component is responsible (" + "; ".join(sorted({f.category for f in unresolved})) + ")"
        elif repeat:
            why = f"the one automatic repair for {len(repeat)} mismatch(es) was used and they remain"
        elif rounds >= m.settings.get("max_repair_rounds", 1):
            why = "the bounded number of repair rounds was used"
        decision = consensus.decide(conflict.proposals, m.settings.get("priorities") or None) if why is None else \
            {"outcome": "escalate", "reason": why, "method": "repair rules: one responsible component, one automatic repair per mismatch"}
        if why is None and decision["outcome"] != "selected":
            why = decision.get("reason")
        conflict.decision = decision
        if why is None:
            chosen = next(p for p in conflict.proposals if p.id == decision["selected"])
            conflict.status = "resolving"
            conflicts.append(conflict)
            self._save_integration(project_id, mission_id, t, conflicts, report)
            self._message(project_id, mission_id, t.agent, "raise_conflict", detail, task_id=t.id,
                          evidence_refs=[x for x in (run.get("id"), routes_a and routes_a.id, calls_a and calls_a.id) if x])
            self._message(project_id, mission_id, t.agent, "propose_resolution", f"{chosen.title} ({decision['reason']})",
                          task_id=t.id, recipient=chosen.action.split(":")[1] + "_agent", proposed_action=chosen.action)
            request = (f"Integration Agent repair request: the {chosen.action.split(':')[1]} departs from the agreed contract "
                       f"(version {m.contract.revision()}). {self._evidence_text([f for f in verified if f.responsible == responsible[0]])}\n"
                       "Follow the contract exactly (method, path, parameters, request body, status codes, response body).")
            self._phase(project_id, mission_id, "REPAIR_REQUIRED", f"{chosen.action}: {len(verified)} verified mismatch(es)")
            self.store.update(project_id, "missions", mission_id,
                              lambda x: self._apply_resolution(x, chosen.action, request, "integration_agent",
                                                               [f for f in x.findings if f.id in {g.id for g in verified}]))
            return {"status": "requeued"}
        conflict.status = "escalated"
        conflicts.append(conflict)
        self._save_integration(project_id, mission_id, t, conflicts, report)
        self._message(project_id, mission_id, t.agent, "raise_conflict", detail, task_id=t.id)
        self._tm(project_id, mission_id, "approval_requested", "Integration Agent", f"needs a person: {why[:200]}", "inconclusive")
        repeat_set = set(repeat)

        def wait(x: Mission):
            for f in x.findings:
                if f.round == round_no and f.status in ("verified", "unresolved"):
                    f.status = "repair_failed" if f.key in repeat_set else "needs_human_review"
            tt = next(y for y in x.tasks if y.id == t.id)
            tt.status, tt.error = "awaiting_review", f"waiting for a person: {why}"
            x.status, x.outcome = "awaiting_decision", "NEEDS_HUMAN_REVIEW"
        self.store.update(project_id, "missions", mission_id, wait)
        self._phase(project_id, mission_id, "AUTOPILOT_REVIEW", why)
        self._report(project_id, mission_id)
        self._review(project_id, mission_id)
        return {"status": "requeued"}

    def _record_repair_results(self, project_id, mission_id, be: Optional[Artifact], fe: Optional[Artifact]) -> None:
        """A pending repair whose component produced a new version: author, time, changed files."""
        def change(x: Mission):
            for r in x.repairs:
                if r.outcome != "pending" or r.artifact_after:
                    continue
                new = be if r.component == "backend" else fe
                if new is None or new.id == r.artifact_before:
                    continue
                old = next((a for a in x.artifacts if a.id == r.artifact_before), None)
                old_files = (old.content.get("files") if old else {}) or {}
                r.artifact_after, r.author = new.id, new.creator
                r.changed_files = sorted(k for k, v in new.content["files"].items() if old_files.get(k) != v)
                r.completed_at = now_iso()
                r.validation = {**r.validation, "new_version_supersedes": new.supersedes,
                                "re_extracted": "route_inventory" if r.component == "backend" else "client_calls"}
        self.store.update(project_id, "missions", mission_id, change)

    def _runtime_run(self, project_id, mission_id, snapshot: Path, contract, routes, fe: Optional[Artifact], round_no: int,
                     arts: Dict[str, Optional[str]]) -> Dict[str, Any]:
        from backend.evolution.autopilot.workspace import create_workspace, discard_workspace
        from backend.swarm import runtime as rt
        m = self._get(project_id, mission_id)
        files = self._integrated_files(m)
        exports = interfaces.client_exports({k: v for k, v in (fe.content["files"] if fe else {}).items()})
        ws = create_workspace(snapshot, prefix="aiforge_swarm_runtime_")
        try:
            for rel, c in files.items():
                (ws / rel).parent.mkdir(parents=True, exist_ok=True)
                (ws / rel).write_text(c, encoding="utf-8", newline="")
            runtime = self.runtime() if self.runtime else rt.DockerRuntime()
            run = rt.run_contract_tests(runtime, ws, files, contract, routes, exports, self.require_isolation)
        finally:
            discard_workspace(ws)
        run.update(id="rt_" + uuid.uuid4().hex[:10], round=round_no, at=now_iso(), artifacts={k: v for k, v in arts.items() if v})
        self.store.update(project_id, "missions", mission_id, lambda x: x.runtime.append(run))
        self._artifact(project_id, mission_id, next(x for x in m.tasks if x.id == "t5"), "integration_agent", "test_report",
                       {"runtime_run": run["id"], "status": run["status"], "counts": run.get("counts"),
                        "environment": run.get("environment")}, m.base_revision)
        return run

    def _save_integration(self, project_id, mission_id, t, conflicts, report) -> None:
        def add(x: Mission):
            x.conflicts.extend(conflicts)
        self.store.update(project_id, "missions", mission_id, add)
        self._artifact(project_id, mission_id, t, t.agent, "integration_report", report, self._get(project_id, mission_id).base_revision)

    def _proposals(self, be_dev, fe_dev, bad, routes, calls) -> List[Proposal]:
        """Competing resolutions, scored only from checked facts (deviations from the contract, change size)."""
        n_calls, n_routes = max(1, len(calls)), max(1, len(routes))
        fix_client = Proposal(
            id="p_client", author="integration_agent", title="Repair the frontend client to the contract",
            action="repair:frontend", evidence=[f"client deviations from the contract: {fe_dev or 'none'}",
                                                f"backend deviations from the contract: {be_dev or 'none'}"],
            requirements_addressed=["the agreed API contract"] if not be_dev else [],
            risks=["if the backend is the side that is wrong, the client would adopt the wrong interface"],
            scores={"contract_conformance": 1.0 if not be_dev else 0.0, "correctness_evidence": 0.5,
                    "security": 1.0, "change_cost": 1 - len(bad) / n_calls, "maintainability": 0.5},
            violates=["the backend departs from the agreed contract"] if be_dev and not fe_dev else [])
        fix_backend = Proposal(
            id="p_backend", author="integration_agent", title="Repair the backend to the contract",
            action="repair:backend", evidence=fix_client.evidence,
            requirements_addressed=["the agreed API contract"] if not fe_dev else [],
            risks=["changing the backend can break its existing tests and other consumers"],
            scores={"contract_conformance": 1.0 if not fe_dev else 0.0, "correctness_evidence": 0.5,
                    "security": 0.8, "change_cost": 1 - len(bad) / n_routes, "maintainability": 0.5},
            violates=["the client departs from the agreed contract"] if fe_dev and not be_dev else [])
        out = [fix_client, fix_backend]
        if be_dev and fe_dev:
            out.append(Proposal(
                id="p_both", author="integration_agent", title="Repair both components to the contract", action="repair:both",
                evidence=fix_client.evidence, requirements_addressed=["the agreed API contract"],
                risks=["both components change; only a person may choose this (both depart from the contract)"],
                scores={"contract_conformance": 1.0, "correctness_evidence": 0.5, "security": 0.9, "change_cost": 0.0,
                        "maintainability": 0.5}))
        return out

    # --- verification gates ------------------------------------------------------------------------------------------------

    def _do_verification(self, project_id, mission_id, t: Task, snapshot: Path) -> Dict[str, Any]:
        from backend.evolution.autopilot import validation
        from backend.evolution.autopilot.workspace import create_workspace, discard_workspace
        m = self._get(project_id, mission_id)
        files = self._integrated_files(m)
        report = self._latest(m, "t5", "integration_report")
        ws = create_workspace(snapshot, prefix="aiforge_swarm_integration_")
        gates: List[Gate] = []
        try:
            for rel, c in files.items():
                (ws / rel).parent.mkdir(parents=True, exist_ok=True)
                (ws / rel).write_text(c, encoding="utf-8", newline="")
            calls = report.content["calls"] if report else []
            contract_ok = bool(calls) and all(c["status"] == "ok" for c in calls)
            gates.append(Gate(name="interface compatibility", mandatory=True, status="passed" if contract_ok else "failed",
                              detail=f"{sum(c['status'] == 'ok' for c in calls)}/{len(calls)} client calls match a backend route",
                              evidence={"integration_report": report.id if report else None}))
            cov = interfaces.check_contract([e.model_dump() for e in m.contract.endpoints], report.content["routes"] if report else [],
                                            [c for c in calls])
            drift = cov["not_implemented"] + cov["not_in_contract_client"] + cov["field_drift_backend"] + cov["field_drift_client"]
            # two components that agree with each other but not with the contract are not correct
            gates.append(Gate(name="contract conformance", mandatory=True, status="failed" if drift else "passed",
                              detail="; ".join(drift) or "every contract operation is implemented and called as agreed",
                              evidence={"coverage": cov}))
            run = m.runtime[-1] if m.runtime else {}
            current = {a.id for a in (self._latest(m, "t2", "source_files"), self._latest(m, "t3", "source_files")) if a}
            tested = set((run.get("artifacts") or {}).get(k) for k in ("backend_artifact", "frontend_artifact")) - {None}
            counts = run.get("counts") or {}
            if not run or run.get("status") in ("blocked", "timeout", "error"):
                rstatus = "unavailable"
            elif tested != current:
                rstatus = "failed"
            elif counts.get("flaky"):
                rstatus = "flaky"
            elif run.get("status") == "completed" and run.get("checks") and set(counts) == {"passed"}:
                rstatus = "passed"
            else:
                rstatus = "failed"
            gates.append(Gate(name="runtime contract tests", mandatory=True, status=rstatus,
                              detail=(f"{counts} in {run.get('environment')}" if run else "no runtime run")
                                     + ("" if tested == current else "; the run did not test the current artifact versions"),
                              evidence={"runtime_run": run.get("id"), "counts": counts, "rerun": run.get("rerun", False),
                                        "tested_artifacts": sorted(tested)}))
            iso, cleanup = run.get("isolation") or {}, run.get("cleanup") or {}
            if self.require_isolation:
                gates.append(Gate(name="isolation and cleanup", mandatory=True,
                                  status="passed" if iso.get("verified") and cleanup.get("verified") else
                                  "unavailable" if not iso else "failed",
                                  detail="; ".join(f"{c['check']}: {'ok' if c['passed'] else 'FAILED'}" for c in iso.get("checks", []))
                                         + f"; cleanup: {cleanup.get('done')} (verified: {cleanup.get('verified')})",
                                  evidence={"isolation": iso, "cleanup": cleanup, "runtime_run": run.get("id")}))
            else:
                gates.append(Gate(name="isolation and cleanup", mandatory=False, status="not_applicable",
                                  detail="isolation requirement disabled by the test harness for a test-only runtime "
                                         f"({run.get('environment')}); such a mission is never run by the application",
                                  evidence={"isolation": iso, "cleanup": cleanup}))
            test_file = self._contract_test(ws, calls)
            if test_file:
                files_for_test = {test_file: (ws / test_file).read_text(encoding="utf-8")}
                self._artifact(project_id, mission_id, t, t.agent, "source_files",
                               {"files": files_for_test, "owned_paths": ["tests/"]}, m.base_revision)
            tests = validation.check_tests(ws)
            status = "passed" if tests.status == "passed" else "failed" if tests.status == "failed" else "unavailable"
            evidence = {"counts": tests.counts, "environment": tests.environment, "output_tail": redact(tests.output[-1500:])}
            if status == "failed":
                rerun = validation.check_tests(ws)            # a failure is re-run once to tell flaky from broken
                evidence["rerun"] = {"status": rerun.status, "counts": rerun.counts}
                if rerun.status == "passed":
                    status = "flaky"                          # not a pass: a mandatory gate needs a reliable result
            gates.append(Gate(name="project and contract tests", mandatory=True, status=status,
                              detail=f"{tests.status}: {tests.counts} ({tests.environment})"
                                     + (f"; re-run: {evidence['rerun']['status']}" if "rerun" in evidence else ""),
                              evidence=evidence))
            after = [r.id for r in m.repairs]
            try:
                sec = self._security_new(project_id, snapshot, files)
                gates.append(Gate(name="security (no new critical/high)", mandatory=True, status="failed" if sec else "passed",
                                  detail=("; ".join(sec) or "no new critical/high Security Guardian finding in the changed files")
                                         + (f" (re-checked after repair(s) {', '.join(after)})" if after else ""),
                                  evidence={"new": sec, "rechecked_after_repairs": after, "files": sorted(files)}))
                if sec:
                    self._security_findings(project_id, mission_id, sec)
            except Exception as e:  # noqa: BLE001
                gates.append(Gate(name="security (no new critical/high)", mandatory=True, status="unavailable",
                                  detail=f"Security Guardian could not run: {type(e).__name__}",
                                  evidence={"rechecked_after_repairs": after}))
            gates.append(Gate(name="performance", mandatory=False, status="not_applicable",
                              detail="not selected for an API-contract mission (no measured baseline exists for new endpoints)"))
            gates.append(Gate(name="resilience", mandatory=False, status="not_applicable",
                              detail="not selected: the components have no external dependency to fail"))
            self._artifact(project_id, mission_id, t, t.agent, "test_report",
                           {"gates": [g.model_dump() for g in gates], "tests": {"status": tests.status, "counts": tests.counts}},
                           m.base_revision)
        finally:
            discard_workspace(ws)
        def save(x: Mission):
            x.gates = gates
            for r in x.repairs:                          # every mandatory gate ran again after the repair
                r.validation = {**r.validation, "gates_after_repair": {g.name: g.status for g in gates if g.mandatory},
                                "security_after_repair": next((g.status for g in gates if g.name.startswith("security")), None)}
                if r.outcome == "succeeded" and any(g.mandatory and g.status != "passed" for g in gates):
                    r.validation["note"] = "the mismatch was repaired, but a mandatory gate did not pass afterwards"
        self.store.update(project_id, "missions", mission_id, save)
        self._tm(project_id, mission_id, "test_executed", "Testing Agent",
                 "; ".join(f"{g.name}: {g.status}" for g in gates if g.mandatory),
                 "success" if all(g.status == "passed" for g in gates if g.mandatory) else "failure",
                 data={"gates": [g.model_dump() for g in gates]})
        failed = [g for g in gates if g.mandatory and g.status != "passed"]
        if failed:
            return {"status": "failed", "error": "mandatory gate(s) did not pass: " + ", ".join(f"{g.name} ({g.status})" for g in failed)}
        return {"status": "completed"}

    def _security_findings(self, project_id: str, mission_id: str, sec: List[str]) -> None:
        """New critical/high Security Guardian findings become security_violation findings. They are never repaired
        automatically: a person decides (Guardian static rules are not called 'verified' vulnerabilities)."""
        def add(x: Mission):
            for s in sec:
                comp = "frontend" if "frontend/" in s else "backend"
                x.findings.append(Finding(id="fd_" + uuid.uuid4().hex[:10], mission_id=mission_id, key=f"security_violation|{s}",
                                          endpoint=s, component=comp, category="security_violation", severity="critical",
                                          expected="no new critical/high Security Guardian finding",
                                          observed=f"Security Guardian static rule: {s}", basis="security",
                                          evidence={"gate": "security (no new critical/high)"}, responsible=comp,
                                          confidence="medium", status="needs_human_review",
                                          recommended_correction="a person reviews the Security Guardian finding (static rule; not verified by exploitation)"))
        self.store.update(project_id, "missions", mission_id, add)

    @staticmethod
    def _contract_test(ws: Path, calls: List[Dict[str, Any]]) -> Optional[str]:
        """A pytest file that sends every client call to the backend (TestClient) and checks it is accepted
        (not 404/405/422, no server error). Values come from the backend model's field types."""
        import re as _re
        from backend.guardian.regression import app_module
        module = app_module(ws)
        if module is None or not calls:
            return None
        lines = ['"""Contract test generated by AIForge Swarm Intelligence: every frontend client call must be accepted',
                 'by the backend exactly as the client sends it."""', "import os", "import tempfile", "",
                 'os.environ.setdefault("DB_PATH", os.path.join(tempfile.mkdtemp(), "contract.db"))', "",
                 "from fastapi.testclient import TestClient  # noqa: E402", "", f"from {module} import app  # noqa: E402", "",
                 "client = TestClient(app)", ""]
        for i, c in enumerate(calls):
            route = c.get("route") or {}
            path = _re.sub(r"\{[^}]*\}", "1", c["path"] or "/")
            body = ({f: _example((route.get("field_types") or {}).get(f, "str")) for f in c["body_fields"]}
                    if c.get("body_fields") is not None else None)
            name = _re.sub(r"[^a-z0-9]+", "_", f"{c['method']} {c['path']}".lower()).strip("_")[:50]
            lines += ["", f"def test_client_call_{i}_{name}_is_accepted():",
                      f"    # {c['file']}:{c['line']} sends {c['method']} {c['path']}",
                      f"    response = client.request({c['method']!r}, {path!r}" + (f", json={body!r}" if body is not None else "") + ")",
                      "    assert response.status_code not in (404, 405, 422) and response.status_code < 500, response.text", ""]
        rel = "tests/test_swarm_contract.py"
        (ws / "tests").mkdir(exist_ok=True)
        (ws / rel).write_text("\n".join(lines), encoding="utf-8")
        return rel


global_swarm_engine = SwarmEngine()
