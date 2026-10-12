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
  integrate   ownership and file conflicts, interface matching (interfaces.match); a mismatch where exactly one
              side departs from the contract is repaired by that side (one bounded round); anything else becomes
              competing proposals decided by consensus.decide, or by a person when tied / unsupported
  verify      project tests + a generated contract test in the Docker sandbox, Security Guardian re-check; a
              mandatory gate that fails or cannot run fails the mission, whatever the agents reported
  deliver     the integrated files become an Autopilot plan awaiting approval (never written directly)
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
from backend.swarm import consensus, interfaces, registry
from backend.swarm.models import Artifact, Conflict, Contract, Gate, Message, Mission, Proposal, Task

_logger = logging.getLogger("aiforge.swarm")
DEFAULTS = {"concurrency": 2, "max_messages": 200, "max_repair_rounds": 1, "mission_seconds": 3600, "priorities": {}}
BACKEND_PROMPT = ("You are AIForge's Backend Agent. Implement exactly the API contract below in FastAPI, with Pydantic "
                  "request models whose fields are the contract's request fields, and pytest tests using "
                  "fastapi.testclient for every endpoint. Return each file as '### path' and a fenced code block.")
FRONTEND_PROMPT = ("You are AIForge's Frontend Agent. Write a JavaScript module frontend/src/api/client.js with one "
                   "exported async function per contract endpoint, using fetch with the contract's exact method, path "
                   "and JSON body fields. Return the file as '### path' and a fenced code block.")


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
                 generate: Optional[Callable[[str, str], str]] = None):
        self.store = store or SwarmStore()
        self.background = background
        self.generate = generate               # None: the local coding model; tests inject fixed agent answers
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
        if m.status not in ("planned", "interrupted", "awaiting_decision"):
            raise SwarmError(f"the mission is '{m.status}'")
        if not approved:
            raise SwarmError("agents generate code that is run in the sandbox: approve the mission explicitly")
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
            self._apply_resolution(x, p.action, f"decided by {user_id}: {p.title}")
        self.store.update(project_id, "missions", mission_id, change)
        self._message(project_id, mission_id, f"user {user_id}", "propose_resolution", f"decision: {p.title}", task_id="t5")
        self._tm(project_id, mission_id, "approval_granted", f"user {user_id}", f"conflict {conflict_id}: {p.title}", "success")
        return self.run(project_id, project, user_id, mission_id, approved=True)

    def deliver(self, project_id: str, user_id: str, mission_id: str) -> Mission:
        """The integrated files as an Autopilot plan awaiting approval; nothing is written to the project here."""
        from backend.evolution.autopilot.models import Plan, PlanTask
        from backend.evolution.autopilot.plans import STRATEGY_AGENT
        from backend.evolution.autopilot.service import global_autopilot_service
        m = self._get(project_id, mission_id)
        if m.status != "completed":
            raise SwarmError("only a mission whose mandatory gates passed can be delivered")
        files = self._integrated_files(m)
        plan = Plan(id="pln_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id,
                    objective=f"Swarm mission: {m.objective[:120]}", finding_ids=[],
                    tasks=[PlanTask(id="t1", title="apply the integrated swarm output", finding_ids=[], files=sorted(files),
                                    strategy="write_files", agent=STRATEGY_AGENT["write_files"],
                                    modification=f"files from mission {mission_id}", contents=files)],
                    expected_files=sorted(files), agents=sorted({t.agent for t in m.tasks if t.agent}),
                    checks=["python_syntax", "quality_gate", "security_static", "tests"],
                    risks=["generated code: review the diff before approving"],
                    assumptions=[f"verified in an isolated workspace by mission {mission_id}"],
                    approval_required=["apply the swarm's integrated files"],
                    completion_criteria=["the project's tests pass with the files applied"], origin="swarm", origin_ref=mission_id)
        global_autopilot_service.store.put(project_id, "plans", plan)
        self.store.update(project_id, "missions", mission_id, lambda x: setattr(x, "delivery", {
            "autopilot_plan_id": plan.id, "files": sorted(files), "status": "awaiting approval in Autopilot"}))
        self._tm(project_id, mission_id, "approval_requested", "Swarm Intelligence",
                 f"delivery plan {plan.id} awaiting approval ({len(files)} files)", "info")
        return self._get(project_id, mission_id)

    def active(self, project_id: str) -> Optional[str]:
        with self._lock:
            return self._active.get(project_id)

    # --- helpers -------------------------------------------------------------------------------------------------

    def _get(self, project_id: str, mission_id: str) -> Mission:
        m = self.store.get(project_id, "missions", mission_id)
        if m is None:
            raise KeyError(mission_id)
        return m

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
        self.store.update(project_id, "missions", mission_id, change)
        self._report(project_id, mission_id)

    def _conclude(self, project_id, mission_id) -> None:
        m = self._get(project_id, mission_id)
        mandatory = [g for g in m.gates if g.mandatory]
        ok = all(t.status == "completed" for t in m.tasks) and mandatory and all(g.status == "passed" for g in mandatory)
        open_conflicts = [c for c in m.conflicts if c.status in ("open", "escalated")]
        status = "completed" if ok and not open_conflicts else "failed"
        why = None if status == "completed" else (
            "unresolved conflicts" if open_conflicts else
            "a mandatory gate did not pass" if mandatory and not all(g.status == "passed" for g in mandatory) else
            "not every task completed")
        self.store.update(project_id, "missions", mission_id, lambda x: (
            setattr(x, "status", status), setattr(x, "error", why), setattr(x, "finished_at", now_iso())))
        self._report(project_id, mission_id)
        self._tm(project_id, mission_id, "task_completed" if status == "completed" else "task_failed", "Swarm Intelligence",
                 f"mission {status}" + (f": {why}" if why else ""), "success" if status == "completed" else "failure")

    def _report(self, project_id, mission_id) -> None:
        m = self._get(project_id, mission_id)
        rep = {
            "status": m.status, "error": m.error,
            "completed_tasks": [t.id + " " + t.objective for t in m.tasks if t.status == "completed"],
            "failed_tasks": [f"{t.id} {t.objective}: {t.error}" for t in m.tasks if t.status in ("failed", "blocked", "cancelled")],
            "unresolved_conflicts": [c.detail for c in m.conflicts if c.status in ("open", "escalated")],
            "resolved_conflicts": [{"detail": c.detail, "decision": c.decision} for c in m.conflicts if c.status == "resolved"],
            "gates": [g.model_dump() for g in m.gates],
            "artifacts": [{"id": a.id, "kind": a.kind, "creator": a.creator, "task": a.task_id, "validation": a.validation}
                          for a in m.artifacts],
            "messages": len(m.messages),
            "limitations": ["response bodies are not compared with the contract (request side only)",
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
        return handler(project_id, mission_id, t, snapshot)

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

    def _apply_resolution(self, x: Mission, action: str, why: str) -> None:
        """Requeue the side that must change (with the reason as feedback), then review and integration again."""
        side = action.split(":", 1)[1] if action.startswith("repair:") else None
        tid = {"frontend": "t3", "backend": "t2"}.get(side)
        if tid is None:
            return
        rounds = x.settings.get("_repair_rounds", 0) + 1
        x.settings["_repair_rounds"] = rounds
        for t in x.tasks:
            if t.id == tid:
                t.status, t.feedback, t.attempts = "pending", why, 0
            elif t.id in ("t4", "t5", "t6"):
                t.status, t.error = "pending", None

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
        # 2. interfaces
        routes, calls = (routes_a.content["items"] if routes_a else []), (calls_a.content["items"] if calls_a else [])
        matched = interfaces.match(calls, routes)
        bad = [c for c in matched if c["status"] != "ok"]
        contract = [e.model_dump() for e in m.contract.endpoints]
        be_dev, fe_dev = interfaces.sides(contract, routes, calls)
        report = {"calls": matched, "routes": routes, "backend_deviations": be_dev, "client_deviations": fe_dev,
                  "file_owners": owners}
        if bad:
            detail = "; ".join(f"{c['method']} {c['path']} ({c['file']}:{c['line']}): {c['reason']}" for c in bad)
            conflict = Conflict(id="cf_" + uuid.uuid4().hex[:8], kind="api_contract", severity="high",
                                components=["t2 backend", "t3 frontend client"], detail=detail,
                                evidence={"mismatches": bad, "backend_deviations": be_dev, "client_deviations": fe_dev,
                                          "route_inventory": routes_a.id if routes_a else None, "client_calls": calls_a.id if calls_a else None})
            conflict.proposals = self._proposals(be_dev, fe_dev, bad, routes, calls)
            rounds = m.settings.get("_repair_rounds", 0)
            decision = consensus.decide(conflict.proposals, m.settings.get("priorities") or None)
            conflict.decision = decision
            if decision["outcome"] == "selected" and rounds < m.settings.get("max_repair_rounds", 1):
                chosen = next(p for p in conflict.proposals if p.id == decision["selected"])
                conflict.status = "resolving"
                conflicts.append(conflict)
                self._save_integration(project_id, mission_id, t, conflicts, report)
                self._message(project_id, mission_id, t.agent, "raise_conflict", detail, task_id=t.id,
                              evidence_refs=[x for x in (routes_a and routes_a.id, calls_a and calls_a.id) if x])
                self._message(project_id, mission_id, t.agent, "propose_resolution", f"{chosen.title} ({decision['reason']})",
                              task_id=t.id, recipient=chosen.action.split(":")[1] + "_agent", proposed_action=chosen.action)
                self.store.update(project_id, "missions", mission_id,
                                  lambda x: self._apply_resolution(x, chosen.action, f"Integration Agent: {detail}. Follow the contract exactly."))
                return {"status": "requeued"}
            conflict.status = "escalated"
            conflict.decision = {**decision, "reason": decision.get("reason") if decision["outcome"] == "escalate"
                                 else "the bounded repair round was used and the mismatch remains"}
            conflicts.append(conflict)
            self._save_integration(project_id, mission_id, t, conflicts, report)
            self._message(project_id, mission_id, t.agent, "raise_conflict", detail, task_id=t.id)
            self._tm(project_id, mission_id, "approval_requested", "Integration Agent", f"conflict needs a decision: {detail[:200]}", "inconclusive")

            def wait(x: Mission):
                tt = next(y for y in x.tasks if y.id == t.id)
                tt.status, tt.error = "awaiting_review", "waiting for a person to decide the conflict"
                x.status = "awaiting_decision"
            self.store.update(project_id, "missions", mission_id, wait)
            return {"status": "requeued"}
        if any(c.kind == "file_ownership" for c in conflicts):
            self._save_integration(project_id, mission_id, t, conflicts, report)
            return {"status": "failed", "error": "file ownership conflicts: " + "; ".join(c.detail for c in conflicts)}
        # previously open api conflicts are now resolved by the repaired artifacts
        self.store.update(project_id, "missions", mission_id, lambda x: [
            (setattr(c, "status", "resolved"), setattr(c, "decision", {**(c.decision or {}), "verified": "the repaired components now match"}))
            for c in x.conflicts if c.kind == "api_contract" and c.status in ("resolving", "escalated")])
        self._save_integration(project_id, mission_id, t, conflicts, report)
        return {"status": "completed"}

    def _save_integration(self, project_id, mission_id, t, conflicts, report) -> None:
        def add(x: Mission):
            x.conflicts.extend(conflicts)
        self.store.update(project_id, "missions", mission_id, add)
        self._artifact(project_id, mission_id, t, t.agent, "integration_report", report, self._get(project_id, mission_id).base_revision)

    def _proposals(self, be_dev, fe_dev, bad, routes, calls) -> List[Proposal]:
        """Competing resolutions, scored only from checked facts (deviations from the contract, change size)."""
        n_calls, n_routes = max(1, len(calls)), max(1, len(routes))
        fix_client = Proposal(
            id="p_client", author="integration_agent", title="Change the frontend client to the backend's interface",
            action="repair:frontend", evidence=[f"client deviations from the contract: {fe_dev or 'none'}",
                                                f"backend deviations from the contract: {be_dev or 'none'}"],
            requirements_addressed=["the agreed API contract"] if not be_dev else [],
            risks=["if the backend is the side that is wrong, the client would adopt the wrong interface"],
            scores={"contract_conformance": 1.0 if not be_dev else 0.0, "correctness_evidence": 0.5,
                    "security": 1.0, "change_cost": 1 - len(bad) / n_calls, "maintainability": 0.5},
            violates=["the backend departs from the agreed contract"] if be_dev and not fe_dev else [])
        fix_backend = Proposal(
            id="p_backend", author="integration_agent", title="Change the backend to the client's interface",
            action="repair:backend", evidence=fix_client.evidence,
            requirements_addressed=["the agreed API contract"] if not fe_dev else [],
            risks=["changing the backend can break its existing tests and other consumers"],
            scores={"contract_conformance": 1.0 if not fe_dev else 0.0, "correctness_evidence": 0.5,
                    "security": 0.8, "change_cost": 1 - len(bad) / n_routes, "maintainability": 0.5},
            violates=["the client departs from the agreed contract"] if fe_dev and not be_dev else [])
        return [fix_client, fix_backend]

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
            try:
                sec = self._security_new(project_id, snapshot, files)
                gates.append(Gate(name="security (no new critical/high)", mandatory=True, status="failed" if sec else "passed",
                                  detail="; ".join(sec) or "no new critical/high Security Guardian finding in the changed files",
                                  evidence={"new": sec}))
            except Exception as e:  # noqa: BLE001
                gates.append(Gate(name="security (no new critical/high)", mandatory=True, status="unavailable",
                                  detail=f"Security Guardian could not run: {type(e).__name__}"))
            gates.append(Gate(name="performance", mandatory=False, status="not_applicable",
                              detail="not selected for an API-contract mission (no measured baseline exists for new endpoints)"))
            gates.append(Gate(name="resilience", mandatory=False, status="not_applicable",
                              detail="not selected: the components have no external dependency to fail"))
            self._artifact(project_id, mission_id, t, t.agent, "test_report",
                           {"gates": [g.model_dump() for g in gates], "tests": {"status": tests.status, "counts": tests.counts}},
                           m.base_revision)
        finally:
            discard_workspace(ws)
        self.store.update(project_id, "missions", mission_id, lambda x: setattr(x, "gates", gates))
        self._tm(project_id, mission_id, "test_executed", "Testing Agent",
                 "; ".join(f"{g.name}: {g.status}" for g in gates if g.mandatory),
                 "success" if all(g.status == "passed" for g in gates if g.mandatory) else "failure",
                 data={"gates": [g.model_dump() for g in gates]})
        failed = [g for g in gates if g.mandatory and g.status != "passed"]
        if failed:
            return {"status": "failed", "error": "mandatory gate(s) did not pass: " + ", ".join(f"{g.name} ({g.status})" for g in failed)}
        return {"status": "completed"}

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
