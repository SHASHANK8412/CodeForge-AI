"""
The Autonomous Integration & Compatibility Engine.

  contracts   register(project, contract, author, reason): validated; a new version only when the content changed
              (revision hash), with a ContractChange (diff, breaking / compatible, affected components and code).
              Versions are kept; nothing overwrites an earlier version. derive() builds the first version from the
              architect's output (the generation workflow does this before the code agents run).
  analyze     the project's files are read (never executed) and checked against the current contract; drift is
              measured against the previous run. Static evidence only, so the result is at best
              COMPATIBLE_WITH_WARNINGS ("the integration tests were not executed").
  verify      on an isolated working copy: analyze, generate the contract tests, run them in the Guardian's isolated
              runner, then the bounded repair loop - pick the responsible agent (contract decisions first, then
              database -> backend -> frontend), apply a targeted fix (deterministic first, the agent's model repair
              otherwise), scope-check it, re-analyse and re-run the tests, roll back a regression, never retry a
              finding that survived its repair. Kept repairs become an Autopilot plan awaiting approval; the project
              itself is never written by an API run.
  workflow    the generation graph's compatibility node: the same loop on the freshly generated project, limited to
              the files this generation's agents wrote (anything else - e.g. an earlier version's files - is never
              changed), with accepted repairs written back through the patch engine.

Final states: COMPATIBLE (a contract exists, every check that applies ran, the generated tests ran and passed, nothing
open), COMPATIBLE_WITH_WARNINGS (nothing blocking, but something was not checked / not executed / only heuristic, or
medium / low findings remain), INCOMPATIBLE (a critical / high finding or a failed contract test), BLOCKED (no
contract, or the tests could not run). Compiling is never evidence of compatibility.
"""

import copy
import logging
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from backend.compatibility import analyzer, extract, repair, testgen
from backend.compatibility import contract as ct
from backend.compatibility.models import (ContractChange, IntegrationRun, RepairRecord, SharedContract)
from backend.evolution.autopilot.models import now_iso
from backend.evolution.autopilot.redact import redact
from backend.evolution.autopilot.store import AutopilotStore

_logger = logging.getLogger("aiforge.compatibility")
DEFAULTS = {"max_repair_attempts": 3, "test_timeout_seconds": 600, "run_seconds": 3600}
BOUNDS = {"max_repair_attempts": (0, 5), "test_timeout_seconds": (60, 1800), "run_seconds": (120, 7200)}
OPEN = ("open", "unresolved", "needs_contract_decision", "blocked")
BLOCKING = ("critical", "high")
STATEMENT = {
    "COMPATIBLE": "every check that applies ran: the contract tests passed and no compatibility finding is open",
    "COMPATIBLE_WITH_WARNINGS": "nothing blocking was found, but not everything was verified: see the warnings",
    "INCOMPATIBLE": "the components do not work together as the contract defines: see the open findings",
    "BLOCKED": "compatibility could not be established: see why",
    "CANCELLED": "the run was cancelled",
}


class ContractError(ValueError):
    def __init__(self, errors: List[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


class Busy(RuntimeError):
    pass


class CompatibilityStore(AutopilotStore):
    KINDS = {"contracts": SharedContract, "changes": ContractChange, "runs": IntegrationRun}
    PRUNE = (("runs", 50, "started_at"),)
    ENV_DIR = "AIFORGE_COMPATIBILITY_DIR"
    DEFAULT_ROOT = Path(__file__).resolve().parents[1] / "data" / "compatibility"


class IntegrationEngine:
    def __init__(self, store: Optional[CompatibilityStore] = None, background: bool = True,
                 generate: Optional[Callable[[str, str], str]] = None,
                 adjudicate: Optional[Callable[[str, str], str]] = None, autopilot=None):
        self.store = store or CompatibilityStore()
        self.background = background
        self.generate = generate               # the agents' model repair (None: the local coding model)
        self.adjudicate = adjudicate           # ambiguous field names (None: deterministic only)
        self.autopilot = autopilot
        self._active: Dict[str, str] = {}
        self._lock = threading.Lock()

    # --- contracts ---------------------------------------------------------------------------------------------------

    def versions(self, project_id: str) -> List[SharedContract]:
        return sorted(self.store.list(project_id, "contracts"), key=lambda c: c.version)

    def current(self, project_id: str) -> Optional[SharedContract]:
        v = self.versions(project_id)
        return v[-1] if v else None

    def version(self, project_id: str, n: int) -> Optional[SharedContract]:
        return self.store.get(project_id, "contracts", f"v{n}")

    def changes(self, project_id: str) -> List[ContractChange]:
        return sorted(self.store.list(project_id, "changes"), key=lambda c: c.to_version)

    def register(self, project_id: str, payload: Any, author: str, reason: str, source: str = "api"
                 ) -> Tuple[SharedContract, Optional[ContractChange], List[str]]:
        """A new contract version (or the current one when nothing changed). Raises ContractError when invalid."""
        if not reason or not reason.strip():
            raise ContractError(["a reason is required for every contract version"])
        data = payload.model_dump(mode="json") if isinstance(payload, SharedContract) else dict(payload or {})
        for k in ("id", "project_id", "version", "revision", "parent_version", "created_at", "author", "reason", "source"):
            data.pop(k, None)
        try:
            c = SharedContract(project_id=project_id, **data)
        except Exception as e:  # noqa: BLE001 - a malformed payload is a validation error, reported as such
            raise ContractError([f"malformed contract: {redact(str(e), 600)}"]) from None
        errors, warnings = ct.validate(c)
        if errors:
            raise ContractError(errors)
        prev = self.current(project_id)
        c.revision = c.compute_revision()
        if prev is not None and prev.revision == c.revision:
            return prev, None, warnings + ["unchanged: the current version already has this content"]
        c.version = (prev.version + 1) if prev else 1
        c.id = f"v{c.version}"
        c.parent_version = prev.version if prev else None
        c.author, c.reason, c.source = author, reason.strip()[:500], source
        last = self.last_run(project_id)
        items = ct.diff(prev, c, (last.implementation if last else None))
        change = ContractChange(id=f"chg_{uuid.uuid4().hex[:10]}", project_id=project_id,
                                from_version=prev.version if prev else None, to_version=c.version,
                                from_revision=prev.revision if prev else None, to_revision=c.revision, author=author,
                                reason=c.reason, source=source, items=items, breaking=any(i.breaking for i in items),
                                affected_components=sorted({x for i in items for x in i.affected_components}))
        self.store.put(project_id, "contracts", c)
        self.store.put(project_id, "changes", change)
        self._tm(project_id, "artifact_generated", f"shared contract v{c.version} registered by {author}"
                 + (" (breaking)" if change.breaking else ""), "info", {"version": c.version, "items": len(items)})
        return c, change, warnings

    def derive(self, project_id: str, arch: Dict[str, Any], plan: Optional[Dict[str, Any]], author: str = "architect",
               reason: str = "derived from the architecture") -> Tuple[SharedContract, Optional[ContractChange], List[str]]:
        return self.register(project_id, ct.derive(project_id, arch, plan), author, reason, source="architect")

    def diff(self, project_id: str, from_v: Optional[int], to_v: Optional[int]) -> Dict[str, Any]:
        cur = self.current(project_id)
        if cur is None:
            raise KeyError("no contract")
        to_c = self.version(project_id, to_v) if to_v else cur
        if to_c is None:
            raise KeyError(f"no contract version {to_v}")
        from_n = from_v if from_v is not None else to_c.parent_version
        from_c = self.version(project_id, from_n) if from_n else None
        if from_v is not None and from_c is None:
            raise KeyError(f"no contract version {from_v}")
        last = self.last_run(project_id)
        items = ct.diff(from_c, to_c, last.implementation if last else None)
        return {"project_id": project_id, "from_version": from_c.version if from_c else None, "to_version": to_c.version,
                "breaking": any(i.breaking for i in items), "items": [i.model_dump() for i in items],
                "history": [h.model_dump() for h in self.changes(project_id)]}

    # --- runs --------------------------------------------------------------------------------------------------------

    @staticmethod
    def settings_of(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        out = dict(DEFAULTS)
        for k, v in (raw or {}).items():
            if k not in BOUNDS:
                raise ContractError([f"unknown setting {k}"])
            lo, hi = BOUNDS[k]
            if not isinstance(v, (int, float)) or isinstance(v, bool) or not lo <= v <= hi:
                raise ContractError([f"setting {k} must be within {lo}-{hi}"])
            out[k] = v
        return out

    def get(self, project_id: str, run_id: str) -> IntegrationRun:
        r = self.store.get(project_id, "runs", run_id)
        if r is None:
            raise KeyError(run_id)
        return r

    def runs(self, project_id: str) -> List[IntegrationRun]:
        return sorted(self.store.list(project_id, "runs"), key=lambda r: r.started_at, reverse=True)

    def last_run(self, project_id: str, exclude: Optional[str] = None) -> Optional[IntegrationRun]:
        done = [r for r in self.runs(project_id) if r.finished_at and r.implementation and r.id != exclude]
        return done[0] if done else None

    def cancel(self, project_id: str, run_id: str) -> IntegrationRun:
        r = self.store.update(project_id, "runs", run_id, lambda x: setattr(x, "cancel_requested", True))
        if r is None:
            raise KeyError(run_id)
        return r

    def _save(self, project_id: str, run_id: str, **fields) -> None:
        def change(x: IntegrationRun):
            for k, v in fields.items():
                setattr(x, k, v)
        self.store.update(project_id, "runs", run_id, change)

    def _activity(self, project_id: str, run_id: str, actor: str, text: str) -> None:
        def add(x: IntegrationRun):
            x.current_operation = text[:200]
            x.activity.append({"at": now_iso(), "actor": actor, "text": redact(text, 600)})
            x.activity = x.activity[-200:]
        self.store.update(project_id, "runs", run_id, add)

    def _tm(self, project_id: str, type_: str, summary: str, outcome: str, data: Optional[Dict[str, Any]] = None) -> None:
        try:
            from backend.time_machine.recorder import emit
            emit(project_id, type_, "Integration Engine", summary, outcome, data=data or {})
        except Exception as e:  # noqa: BLE001 - the ledger is an observer
            _logger.debug("time machine event not recorded: %s", e)

    def _new_run(self, project_id: str, user_id: str, kind: str, source: str, settings: Dict[str, Any]) -> IntegrationRun:
        c = self.current(project_id)
        r = IntegrationRun(id="int_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id, kind=kind, source=source,
                           status="running", settings=settings, contract_version=c.version if c else None,
                           contract_revision=c.revision if c else None)
        self.store.put(project_id, "runs", r)
        return r

    def _previous(self, project_id: str, run_id: str, c: Optional[SharedContract]) -> Optional[Dict[str, Any]]:
        last = self.last_run(project_id, exclude=run_id)
        if not last:
            return None
        items = [i.model_dump() for ch in self.changes(project_id)
                 if (last.contract_version or 0) < ch.to_version <= (c.version if c else 0) for i in ch.items]
        return {"fingerprint": (last.implementation or {}).get("fingerprint"), "contract_revision": last.contract_revision,
                "contract_items": items, "run_id": last.id}

    def _analyse(self, project_id: str, run_id: str, root: Path, c: Optional[SharedContract], previous, adjudicate=None):
        snap = extract.snapshot(root)
        findings, coverage, components = analyzer.analyze(c, snap, previous, adjudicate)
        return snap, findings, coverage, components

    # analyze: static only ---------------------------------------------------------------------------------------------

    def analyze(self, project_id: str, project: Path, user_id: str, source: str = "api") -> IntegrationRun:
        project = Path(project).resolve()
        if not project.is_dir():
            raise ContractError(["the project folder does not exist"])
        r = self._new_run(project_id, user_id, "analyze", source, {})
        c = self.current(project_id)
        try:
            self._activity(project_id, r.id, "Integration Engine", "reading the project's components (nothing is executed)")
            snap, findings, coverage, components = self._analyse(project_id, r.id, project, c, self._previous(project_id, r.id, c),
                                                                 self.adjudicate)
            self._save(project_id, r.id, findings=findings, original_findings=copy.deepcopy(findings), coverage=coverage,
                       components=components, implementation=_impl(snap))
            self._finish(project_id, r.id, c)
        except Exception as e:  # noqa: BLE001 - recorded on the run
            _logger.exception("analysis %s failed", r.id)
            self._save(project_id, r.id, status="BLOCKED", error=redact(f"{type(e).__name__}: {e}", 800), finished_at=now_iso())
            self._report(project_id, r.id, c)
        return self.get(project_id, r.id)

    # verify: tests + bounded repairs on a copy -------------------------------------------------------------------------

    def start_verify(self, project_id: str, project: Path, user_id: str, settings: Optional[Dict[str, Any]] = None) -> IntegrationRun:
        project = Path(project).resolve()
        if not project.is_dir():
            raise ContractError(["the project folder does not exist"])
        if self.current(project_id) is None:
            raise ContractError(["no shared contract is registered for this project: register or derive one first"])
        cfg = self.settings_of(settings)
        with self._lock:
            if project_id in self._active:
                raise Busy(f"integration run {self._active[project_id]} is already running for this project")
            r = self._new_run(project_id, user_id, "verify", "api", cfg)
            self._active[project_id] = r.id

        def go():
            try:
                self._verify(project_id, r.id, project)
            finally:
                with self._lock:
                    self._active.pop(project_id, None)
        if self.background:
            threading.Thread(target=go, name=f"aice-{r.id}", daemon=True).start()
        else:
            go()
        return self.get(project_id, r.id)

    def _verify(self, project_id: str, run_id: str, project: Path, owned: Optional[set] = None, write_back: bool = False,
                allow_model: bool = True) -> None:
        from backend.evolution.autopilot.workspace import create_workspace, discard_workspace, file_hash
        from backend.execution_guardian import checks as chk
        r = self.get(project_id, run_id)
        cfg = r.settings
        c = self.current(project_id)
        deadline = time.monotonic() + float(cfg.get("run_seconds", 3600))

        def stop() -> bool:
            x = self.store.get(project_id, "runs", run_id)
            return bool(x and x.cancel_requested) or time.monotonic() > deadline
        ws = None
        try:
            self._activity(project_id, run_id, "Integration Engine", "copying the project into an isolated working copy")
            ws = create_workspace(project, prefix="aiforge_aice_")
            base = {p.relative_to(ws).as_posix(): file_hash(p) for p in ws.rglob("*") if p.is_file()}
            stack = chk.detect(ws)
            previous = self._previous(project_id, run_id, c)
            snap, findings, coverage, components = self._analyse(project_id, run_id, ws, c, previous, self.adjudicate)
            self._save(project_id, run_id, findings=findings, original_findings=copy.deepcopy(findings), coverage=coverage,
                       components=components, implementation=_impl(snap))
            self._activity(project_id, run_id, "Integration Engine",
                           f"{sum(1 for f in findings if f.status in OPEN)} open finding(s); generating the contract tests")
            tests, files = testgen.generate(c, snap, stack)
            notes = testgen.prepare(ws, files)
            tests, execution = self._run_tests(project_id, run_id, ws, tests, cfg, stack, notes)
            self._repair_loop(project_id, run_id, ws, stack, c, cfg, stop, owned, allow_model, previous)
            r = self.get(project_id, run_id)
            changed = sorted({f for rec in r.repairs if not rec.rolled_back and rec.outcome not in ("rejected", "no_fix", "deferred")
                              for f in rec.files_changed})
            if changed:
                contents = {p: (ws / p).read_text(encoding="utf-8") for p in changed if (ws / p).is_file()}
                if write_back:
                    self._write_back(project_id, run_id, project, contents)
                else:
                    self._deliver(project_id, run_id, contents, {p: base.get(p) for p in contents})
            self._finish(project_id, run_id, c, cancelled=bool(self.get(project_id, run_id).cancel_requested))
        except Exception as e:  # noqa: BLE001 - recorded on the run, never hidden
            _logger.exception("integration run %s failed", run_id)
            self._save(project_id, run_id, status="BLOCKED", error=redact(f"{type(e).__name__}: {e}", 800), finished_at=now_iso(),
                       current_operation="stopped by an internal error")
            self._report(project_id, run_id, c)
        finally:
            if ws is not None:
                discard_workspace(ws)

    def _run_tests(self, project_id, run_id, ws: Path, tests, cfg, stack, notes=None):
        self._activity(project_id, run_id, "Integration Engine", f"running {len(tests)} contract test(s) in isolation")
        tests, execution = testgen.execute(ws, tests, float(cfg.get("test_timeout_seconds", 600)))
        execution["copy_notes"] = (notes or []) + ([] if stack.get("fastapi_app") else
                                                   ["no FastAPI app was found: the API tests fail to import one"])
        self._save(project_id, run_id, tests=tests, test_execution=execution)
        self._activity(project_id, run_id, "Integration Engine",
                       f"contract tests: {execution['status']} ({', '.join(f'{v} {k}' for k, v in execution['counts'].items() if v)})")
        return tests, execution

    def _repair_loop(self, project_id, run_id, ws: Path, stack, c: SharedContract, cfg, stop, owned: Optional[set],
                     allow_model: bool, previous) -> None:
        from backend.evolution.autopilot.executor import apply_all
        exhausted: set = set()
        deferred_noted: set = set()
        for attempt in range(1, int(cfg.get("max_repair_attempts", 3)) + 1):
            if stop():
                return
            r = self.get(project_id, run_id)
            agent, group, deferred = repair.pick(r.findings, exhausted)
            new_deferred = [f for f in deferred if f.key not in deferred_noted]
            if new_deferred:
                deferred_noted |= {f.key for f in new_deferred}
                self._add_repair(project_id, run_id, RepairRecord(
                    attempt=attempt, agent="architect", strategy="contract decision first", finding_keys=[f.key for f in new_deferred],
                    outcome="deferred", finished_at=now_iso(),
                    note="these implementation repairs wait for a contract decision on the same operation"))
            if agent is None:
                self._activity(project_id, run_id, "Integration Engine",
                               "no repairable finding left (contract decisions, heuristics without evidence, or repeated failures): stopping")
                return
            files = extract.read_sources(ws)
            snap = extract.snapshot(ws, files)
            rec = RepairRecord(attempt=attempt, agent=agent, finding_keys=[f.key for f in group],
                               tests_before=_passed(r.tests))
            self._activity(project_id, run_id, f"{agent} agent", f"repair attempt {attempt}: {len(group)} finding(s) "
                           f"({', '.join(sorted({f.rule for f in group}))})")
            changes, strategies, keys = repair.deterministic(group, files, snap, c)
            note = ""
            if not changes and allow_model:
                strategy, changes, note = repair.model_repair(group, agent, ws, stack, c, project_id, self.generate)
                strategies, keys = [strategy], [f.key for f in group]
                if not changes and not note:
                    note = f"no deterministic fix applies, and the {agent} agent's model proposed no change"
            rec.strategy = ", ".join(strategies) or ("model repair disabled" if not allow_model else "none")
            accepted, rejected = repair.validate(changes, agent, stack, ws, group)
            if owned is not None:
                for p in list(accepted):
                    if p not in owned:
                        accepted.pop(p)
                        rejected.append({"path": p, "reason": "not written by this generation's agents: left unchanged"})
            rec.rejected_paths = rejected
            if not accepted:
                rec.outcome = "rejected" if rejected else "no_fix"
                rec.note = note or ("every proposed change was outside the allowed scope" if rejected else
                                    "no deterministic fix applies" + ("" if allow_model else " and model repair is disabled"))
                rec.finished_at = now_iso()
                exhausted |= {f.key for f in group}
                self._add_repair(project_id, run_id, rec)
                continue
            backup = {p: ((ws / p).read_text(encoding="utf-8", errors="replace") if (ws / p).is_file() else None) for p in accepted}
            _, ok = apply_all(ws, accepted, f"Integration Engine repair {attempt} ({agent})")
            if not ok:
                rec.outcome, rec.note, rec.finished_at = "rejected", "the patch engine rejected the change (rolled back)", now_iso()
                exhausted |= {f.key for f in group}
                self._add_repair(project_id, run_id, rec)
                continue
            rec.files_changed = sorted(accepted)
            before_keys = {f.key for f in r.findings if f.status in OPEN}
            # drift is measured once, before any repair: this run's own repairs are not drift
            new_snap, findings, coverage, components = self._analyse(project_id, run_id, ws, c, None, self.adjudicate)
            findings += [f for f in r.findings if f.rule == "contract_drift" and f.key not in {x.key for x in findings}]
            coverage = [x for x in coverage if x["check"] != "contract drift"] + [x for x in r.coverage if x["check"] == "contract drift"]
            tests, execution = r.tests, r.test_execution
            if r.tests:
                regenerated, files_ = testgen.generate(c, new_snap, stack)
                for rel, content in files_.items():
                    (ws / rel).write_text(content, encoding="utf-8")
                tests, execution = self._run_tests(project_id, run_id, ws, regenerated, cfg, stack, execution.get("copy_notes"))
            after_keys = {f.key for f in findings if f.status in OPEN}
            rec.resolved = sorted(before_keys - after_keys)
            rec.new_findings = sorted(after_keys - before_keys)
            rec.tests_after = _passed(tests)
            worse_tests = (rec.tests_after.get("passed", 0) < rec.tests_before.get("passed", 0)
                           or rec.tests_after.get("failed", 0) > rec.tests_before.get("failed", 0))
            if (rec.new_findings and not rec.resolved) or worse_tests:
                apply_all(ws, backup, f"Integration Engine rollback of repair {attempt}")
                rec.rolled_back, rec.outcome = True, "regressed"
                rec.note = "the repair introduced new findings or made contract tests fail: rolled back"
                self._save(project_id, run_id, tests=r.tests, test_execution=r.test_execution)
                exhausted |= set(keys) | {f.key for f in group}
            else:
                attempted = set(keys)
                rec.outcome = ("resolved" if attempted and not (attempted & after_keys) and not rec.new_findings
                               else "improved" if rec.resolved else "no_change")
                exhausted |= attempted & after_keys
                if not rec.resolved:
                    exhausted |= {f.key for f in group}
                # the fresh analysis, plus every finding repaired so far (kept, marked repaired, for the history)
                repaired = [f.model_copy(update={"status": "repaired"}) for f in r.findings
                            if f.key in rec.resolved or f.status == "repaired"]
                self._save(project_id, run_id, findings=findings + repaired, coverage=coverage, components=components,
                           implementation=_impl(new_snap))
            rec.finished_at = now_iso()
            self._add_repair(project_id, run_id, rec)

    def _add_repair(self, project_id: str, run_id: str, rec: RepairRecord) -> None:
        self.store.update(project_id, "runs", run_id, lambda x: x.repairs.append(rec))
        self._activity(project_id, run_id, f"{rec.agent} agent", f"repair {rec.attempt}: {rec.outcome}"
                       + (f" ({', '.join(rec.files_changed)})" if rec.files_changed else "") + (f" - {rec.note}" if rec.note else ""))

    # --- workflow ----------------------------------------------------------------------------------------------------

    def workflow_check(self, project_id: str, project: Path, owned: List[str], allow_model: bool = False,
                       run_tests: bool = True, settings: Optional[Dict[str, Any]] = None) -> IntegrationRun:
        """The generation graph's compatibility node. Without a contract the run is BLOCKED (nothing is assumed)."""
        cfg = self.settings_of(settings)
        c = self.current(project_id)
        r = self._new_run(project_id, "workflow", "verify" if run_tests else "analyze", "workflow", cfg)
        if c is None:
            self._save(project_id, r.id, coverage=[{"check": "contract", "status": "blocked",
                                                    "detail": "no shared contract was established for this generation"}])
            self._finish(project_id, r.id, None)
            return self.get(project_id, r.id)
        if not run_tests:
            snap, findings, coverage, components = self._analyse(project_id, r.id, Path(project), c, self._previous(project_id, r.id, c))
            self._save(project_id, r.id, findings=findings, original_findings=copy.deepcopy(findings), coverage=coverage,
                       components=components, implementation=_impl(snap))
            self._finish(project_id, r.id, c)
            return self.get(project_id, r.id)
        self._verify(project_id, r.id, Path(project), owned=set(owned), write_back=True, allow_model=allow_model)
        return self.get(project_id, r.id)

    def _write_back(self, project_id: str, run_id: str, project: Path, contents: Dict[str, str]) -> None:
        from backend.evolution.autopilot.executor import apply_all
        written, ok = apply_all(project, contents, f"Integration Engine repairs ({run_id})")
        self._save(project_id, run_id, delivery={"written": sorted(contents) if ok else [], "project_modified": bool(ok),
                                                 "status": "written to the generated project" if ok else
                                                 "the patch engine rejected the write (nothing changed)"})

    def _deliver(self, project_id: str, run_id: str, contents: Dict[str, str], base: Dict[str, Optional[str]]) -> None:
        """Kept repairs as an Autopilot plan awaiting approval (the project itself is never written here)."""
        from backend.evolution.autopilot.models import Plan, PlanTask
        from backend.evolution.autopilot.plans import STRATEGY_AGENT
        r = self.get(project_id, run_id)
        plan = Plan(id="pln_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=r.user_id,
                    objective=f"Integration Engine repairs (contract v{r.contract_version})", finding_ids=[],
                    tasks=[PlanTask(id="t1", title="apply the compatibility repairs", finding_ids=[], files=sorted(contents),
                                    strategy="write_files", agent=STRATEGY_AGENT["write_files"],
                                    modification=f"files repaired by {run_id} against contract v{r.contract_version}",
                                    contents=contents)],
                    expected_files=sorted(contents), agents=sorted({x.agent for x in r.repairs if x.files_changed}),
                    checks=["python_syntax", "quality_gate", "security_static", "tests"],
                    risks=["agent repairs: review the diff before approving",
                           "files you changed after this run would be overwritten: compare with the base hashes below"],
                    assumptions=[f"made in an isolated working copy by {run_id}"]
                    + [f"base {p}: sha256 {h}" for p, h in sorted(base.items())],
                    approval_required=["apply the repaired files"],
                    completion_criteria=["a new integration run reports no open blocking finding"],
                    origin="integration_engine", origin_ref=run_id)
        try:
            svc = self.autopilot
            if svc is None:
                from backend.evolution.autopilot.service import global_autopilot_service as svc
            svc.store.put(project_id, "plans", plan)
            self._save(project_id, run_id, delivery={"autopilot_plan_id": plan.id, "files": sorted(contents), "base_hashes": base,
                                                     "status": "awaiting approval in Autopilot", "project_modified": False})
        except Exception as e:  # noqa: BLE001
            self._save(project_id, run_id, delivery={"error": f"the Autopilot plan could not be created: {type(e).__name__}",
                                                     "project_modified": False})

    # --- status and report -------------------------------------------------------------------------------------------

    def _finish(self, project_id: str, run_id: str, c: Optional[SharedContract], cancelled: bool = False) -> None:
        r = self.get(project_id, run_id)
        status, warnings, why = final_status(r, c)
        if cancelled:
            status = "CANCELLED"
        self._save(project_id, run_id, status=status, finished_at=now_iso(), current_operation="finished")
        self._report(project_id, run_id, c, warnings, why)
        self._tm(project_id, "test_executed" if r.kind == "verify" else "review_completed", f"integration {status}",
                 "success" if status.startswith("COMPATIBLE") else "cancelled" if status == "CANCELLED" else "failure",
                 {"run_id": run_id, "findings": sum(1 for f in r.findings if f.status in OPEN)})

    def _report(self, project_id: str, run_id: str, c: Optional[SharedContract], warnings: Optional[List[str]] = None,
                why: Optional[List[str]] = None) -> None:
        r = self.get(project_id, run_id)
        sev = {s: sum(1 for f in r.findings if f.status in OPEN and f.severity == s) for s in ("critical", "high", "medium", "low")}
        originals = {f.key for f in r.original_findings if f.status in OPEN}
        current = {f.key for f in r.findings if f.status in OPEN}
        counts = (r.test_execution or {}).get("counts") or {}
        rep = {
            "project_id": project_id, "run_id": r.id, "kind": r.kind, "source": r.source, "status": r.status,
            "statement": STATEMENT.get(r.status, r.status), "compatible": r.status in ("COMPATIBLE", "COMPATIBLE_WITH_WARNINGS"),
            "contract_version": r.contract_version, "contract_revision": r.contract_revision,
            "components_analyzed": r.components, "coverage": r.coverage,
            "findings_by_severity": sev,
            "findings": [_finding_view(f) for f in r.findings if f.status in OPEN],
            "informational": [_finding_view(f) for f in r.findings if f.status == "info"],
            "drift": [_finding_view(f) for f in r.findings if f.rule == "contract_drift"],
            "repairs": [x.model_dump() for x in r.repairs],
            "repaired": [_finding_view(f) for f in r.original_findings if f.key in originals - current],
            "tests_generated": len(r.tests),
            "tests_executed": sum(v for k, v in counts.items() if k in ("passed", "failed", "error", "skipped")),
            "tests_passed": counts.get("passed", 0), "tests_failed": counts.get("failed", 0) + counts.get("error", 0),
            "tests_skipped": counts.get("skipped", 0), "tests_not_run": counts.get("not_run", 0),
            "test_execution": {k: v for k, v in (r.test_execution or {}).items() if k != "log_excerpt"},
            "tests": [t.model_dump() for t in r.tests],
            "unresolved": [_finding_view(f) for f in r.findings if f.status in OPEN],
            "warnings": warnings or [], "why": why or [], "delivery": r.delivery, "error": r.error,
            "started_at": r.started_at, "finished_at": r.finished_at,
            "limitations": [
                "response fields the frontend reads are found by pattern matching (basis static_heuristic): a read the "
                "pattern misses is not checked, and such findings are not proof on their own",
                "frontend requests are replayed against the backend from the code's method, path and body keys; the "
                "browser itself is not run",
                "SQL schemas are applied to SQLite in memory; PostgreSQL-only schemas are reported as not applied",
            ],
        }
        self._save(project_id, run_id, report=redact_tree(rep))


def final_status(r: IntegrationRun, c: Optional[SharedContract]) -> Tuple[str, List[str], List[str]]:
    """(status, warnings, why). See the module docstring for the rules."""
    if c is None:
        return "BLOCKED", [], ["no shared contract: compatibility cannot be established without one"]
    open_ = [f for f in r.findings if f.status in OPEN]
    blocking = [f for f in open_ if f.severity in BLOCKING]
    ex = r.test_execution or {}
    why: List[str] = []
    if blocking:
        why += [f"{f.severity}: {f.rule} {f.target}" for f in blocking[:10]]
    if ex.get("status") == "FAILED":
        failed = [t for t in r.tests if t.status in ("failed", "error")]
        why += [f"contract test failed: {t.id} ({t.detail[:160]})" for t in failed[:10]]
    if why:
        return "INCOMPATIBLE", [], why
    if r.kind == "verify" and ex.get("status") in (None, "BLOCKED"):
        return "BLOCKED", [], ["the contract tests could not run: " + (ex.get("reason") or ex.get("error_summary") or "not executed")]
    warnings = [f"{f.severity}: {f.rule} {f.target} - {f.actual[:160]}" for f in open_]
    if r.kind == "analyze":
        warnings.append("static analysis only: the generated integration tests were not executed")
    executed_ok = ex.get("status") == "PASSED"
    for cov in r.coverage:
        if cov["status"] in ("not_checked", "blocked"):
            if executed_ok and "generated tests" in cov["detail"]:
                continue
            warnings.append(f"not checked: {cov['check']} ({cov['detail']})")
    if ex.get("counts", {}).get("skipped"):
        warnings.append(f"{ex['counts']['skipped']} contract test(s) were skipped")
    if ex.get("counts", {}).get("not_run"):
        warnings.append(f"{ex['counts']['not_run']} contract test(s) did not run")
    unspec = sorted({f"{k}: {', '.join(v)}" for k, v in (c.unspecified or {}).items() if v})
    if unspec:
        warnings.append("the contract leaves aspects unspecified (not checked): " + "; ".join(unspec[:12]))
    return ("COMPATIBLE_WITH_WARNINGS" if warnings else "COMPATIBLE"), warnings, why


def _passed(tests) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for t in tests or []:
        out[t.status] = out.get(t.status, 0) + 1
    return out


def _impl(snap: Dict[str, Any]) -> Dict[str, Any]:
    """The part of a snapshot stored on the run (drift baseline + code locations for change impact)."""
    return {"fingerprint": snap.get("fingerprint"), "digest": snap.get("digest"),
            "backend": {"routes": [{k: r[k] for k in ("method", "path", "file", "line")} for r in (snap.get("backend") or {}).get("routes", [])]},
            "frontend": {"calls": [{k: c.get(k) for k in ("method", "path", "file", "line")} for c in (snap.get("frontend") or {}).get("calls", [])]}}


def _finding_view(f) -> Dict[str, Any]:
    return f.model_dump(exclude={"detected_at"})


def redact_tree(x: Any) -> Any:
    if isinstance(x, str):
        return redact(x, 4000)
    if isinstance(x, list):
        return [redact_tree(v) for v in x]
    if isinstance(x, dict):
        return {k: redact_tree(v) for k, v in x.items()}
    return x


def markdown(rep: Dict[str, Any]) -> str:
    lines = [f"# Compatibility report - {rep['project_id']}", "",
             f"**Status: {rep['status']}** - {rep['statement']}", "",
             f"- Run: {rep['run_id']} ({rep['kind']}, {rep['source']})",
             f"- Contract: v{rep['contract_version']} (revision {rep['contract_revision']})",
             f"- Tests: {rep['tests_generated']} generated, {rep['tests_executed']} executed, {rep['tests_passed']} passed, "
             f"{rep['tests_failed']} failed, {rep['tests_skipped']} skipped, {rep['tests_not_run']} not run", ""]
    comp = rep.get("components_analyzed") or {}
    lines += ["## Components analyzed", ""]
    for name in ("backend", "frontend", "database"):
        if comp.get(name):
            lines.append(f"- **{name}**: " + ", ".join(f"{k}: {v}" for k, v in comp[name].items() if not isinstance(v, (list, dict)) or v))
    if rep.get("why"):
        lines += ["", "## Why", ""] + [f"- {w}" for w in rep["why"]]
    lines += ["", "## Open findings", ""]
    if not rep["findings"]:
        lines.append("- none")
    for f in rep["findings"]:
        lines += [f"- **{f['severity']}** `{f['rule']}` {f['target']} ({f['basis']}, responsible: {f['responsible_agent'] or 'undecided'})",
                  f"  - expected: {f['expected']}", f"  - actual: {f['actual']}", f"  - fix: {f['recommended_fix']}"]
    if rep.get("drift"):
        lines += ["", "## Contract drift", ""] + [f"- {'BREAKING' if f.get('breaking') else 'compatible'}: {f['target']} - {f['actual']}"
                                                  for f in rep["drift"]]
    lines += ["", "## Repairs", ""] + ([f"- attempt {x['attempt']} ({x['agent']}, {x['strategy']}): {x['outcome']}"
                                        + (f" - {', '.join(x['files_changed'])}" if x['files_changed'] else "")
                                        + (f" - {x['note']}" if x['note'] else "") for x in rep["repairs"]] or ["- none"])
    lines += ["", "## Contract tests", ""] + ([f"- {t['status']}: `{t['id']}` - {t['description']}"
                                              + (f" ({t['detail'][:200]})" if t['detail'] and t['status'] != 'passed' else "")
                                              for t in rep["tests"]] or ["- none generated"])
    lines += ["", "## Not checked", ""] + ([f"- {c['check']}: {c['detail']}" for c in rep["coverage"] if c["status"] != "checked"] or ["- nothing"])
    if rep.get("warnings"):
        lines += ["", "## Warnings", ""] + [f"- {w}" for w in rep["warnings"]]
    lines += ["", "## Limitations", ""] + [f"- {x}" for x in rep["limitations"]]
    return "\n".join(lines) + "\n"


global_integration_engine = IntegrationEngine()
