"""
AIForge Time Machine: engineering history, causal graph, checkpoints, safe restoration, the Regression
Detective, historical replay and experimental reruns - all from the event ledger (ledger.py), which only
holds what subsystems actually reported (recorder.py).

Labels used everywhere: "recorded" (a stored event or link), "temporal" (only ordered in time - an
association, not causation), "reconstructed" (derived from recorded file versions), "rerun" (executed
again now - not a reproduction of the original).
"""

import difflib
import hashlib
import json
import logging
import shutil
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.evolution.autopilot.models import now_iso
from backend.evolution.autopilot.redact import redact
from backend.evolution.autopilot.store import AutopilotStore
from backend.time_machine import state as st
from backend.time_machine.ledger import Event, Ledger
from backend.time_machine.recorder import emit, global_ledger

_logger = logging.getLogger("aiforge.time_machine")
INVESTIGATION_DEADLINE = 1800
MAX_BISECT_RUNS = 12


class TimeMachineError(ValueError):
    pass


class Busy(RuntimeError):
    pass


class Job(BaseModel):
    id: str
    project_id: str
    user_id: str
    kind: str                                   # investigation | rerun
    status: str = "queued"                      # queued | running | completed | failed | cancelled
    created_at: str = Field(default_factory=now_iso)
    finished_at: Optional[str] = None
    target: Dict[str, Any] = Field(default_factory=dict)
    steps: List[Dict[str, Any]] = Field(default_factory=list)    # every test run: state, result, evidence
    result: Dict[str, Any] = Field(default_factory=dict)
    cancel_requested: bool = False
    error: Optional[str] = None


class JobStore(AutopilotStore):
    KINDS = {"jobs": Job}
    PRUNE = (("jobs", 50, "created_at"),)
    ENV_DIR = "AIFORGE_TIME_MACHINE_JOBS_DIR"
    DEFAULT_ROOT = Path(__file__).resolve().parents[1] / "data" / "time_machine" / "jobs"


def _failing_tests(output: str) -> List[str]:
    import re
    return sorted(set(re.findall(r"FAILED\s+(\S+::\S+)", output or "")))[:20]


class TimeMachine:
    def __init__(self, ledger: Optional[Ledger] = None, jobs: Optional[JobStore] = None, background: bool = True):
        self.ledger = ledger or global_ledger
        self._jobs = jobs
        self.background = background
        self._active: Dict[str, str] = {}
        self._lock = threading.Lock()

    @property
    def jobs(self) -> JobStore:
        if self._jobs is None:
            self._jobs = JobStore(self.ledger.root / "jobs")
        return self._jobs

    # --- history -----------------------------------------------------------------------------------------

    def timeline(self, project_id: str, **filters) -> Dict[str, Any]:
        page = self.ledger.query(project_id, **filters)
        page["items"] = [e.model_dump(mode="json") for e in page["items"]]
        page["integrity"] = self.ledger.verify(project_id)
        return page

    def legacy(self, project_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Flight Recorder events (written before the ledger existed): shown read-only, not verified."""
        try:
            from backend.autopilot.recorder import global_flight_recorder
            items = global_flight_recorder.get_events(project_id)[-limit:]
        except Exception:  # noqa: BLE001
            return []
        return [{**{k: redact(str(v), 400) if isinstance(v, str) else v for k, v in e.items()},
                 "provenance": "legacy Flight Recorder: not hash-chained; some emitting subsystems were simulated"}
                for e in reversed(items)]

    def graph(self, project_id: str, task_id: Optional[str] = None, limit: int = 300) -> Dict[str, Any]:
        events = self.ledger.events(project_id)
        if task_id:
            ids = {e.id for e in events if e.task_id == task_id or task_id in e.refs.values()}
            # include recorded ancestors so cross-task causes (e.g. the approval) stay visible
            by_id = {e.id: e for e in events}
            frontier = list(ids)
            while frontier:
                for p in by_id.get(frontier.pop(), Event(id="x", project_id="x", type="correction", source="x")).parents:
                    if p in by_id and p not in ids:
                        ids.add(p)
                        frontier.append(p)
            events = [e for e in events if e.id in ids]
        events = events[-limit:]
        known = {e.id for e in events}
        nodes = [{"id": e.id, "type": e.type, "source": e.source, "summary": e.summary, "outcome": e.outcome, "at": e.at,
                  "task_id": e.task_id, "files": [f["path"] for f in e.files]} for e in events]
        edges = []
        for e in events:
            for p in e.parents:
                if p in known:
                    edges.append({"from": p, "to": e.id, "kind": "recorded"})
        # same task, consecutive, no recorded link: shown as a temporal association only
        by_task: Dict[str, List[Event]] = {}
        for e in events:
            if e.task_id:
                by_task.setdefault(e.task_id, []).append(e)
        linked = {(x["from"], x["to"]) for x in edges}
        for items in by_task.values():
            for a, b in zip(items, items[1:]):
                if (a.id, b.id) not in linked and a.id not in b.parents:
                    edges.append({"from": a.id, "to": b.id, "kind": "temporal",
                                  "note": "ordered in time within the same task; no causal link was recorded"})
        # later changes to the same file
        last_change: Dict[str, str] = {}
        for e in events:
            for f in e.files:
                prev = last_change.get(f["path"])
                if prev and (prev, e.id) not in linked:
                    edges.append({"from": prev, "to": e.id, "kind": "file", "note": f"both changed {f['path']}"})
                last_change[f["path"]] = e.id
        return {"nodes": nodes, "edges": edges,
                "legend": {"recorded": "a causal link the emitting subsystem recorded",
                           "temporal": "only ordered in time (association, not proven causation)",
                           "file": "a later change to the same file"}}

    def replay(self, project_id: str, task_id: str) -> Dict[str, Any]:
        """Historical replay: the recorded steps of a task, with file diffs reconstructed from stored versions.
        Nothing is executed."""
        events = [e for e in self.ledger.events(project_id) if e.task_id == task_id or task_id in e.refs.values()]
        if not events:
            raise KeyError(task_id)
        steps = []
        for e in events:
            diffs = []
            for f in e.files:
                b, a = self.ledger.get_blob(f.get("before")), self.ledger.get_blob(f.get("after"))
                if (f.get("before") and b is None) or (f.get("after") and a is None):
                    diffs.append({"path": f["path"], "available": False,
                                  "reason": "the content was not stored (secret-like values or too large)"})
                    continue
                diffs.append({"path": f["path"], "available": True, "change": f.get("change"),
                              "diff": redact("".join(difflib.unified_diff((b or "").splitlines(True), (a or "").splitlines(True),
                                                                          f"a/{f['path']}", f"b/{f['path']}")), 20000)})
            steps.append({"event": e.model_dump(mode="json"), "diffs": diffs, "provenance": "recorded"})
        gaps = []
        types = [e.type for e in events]
        if "agent_started" in types and not any(t in types for t in ("task_completed", "task_failed")):
            gaps.append("no completion event was recorded (still running, interrupted, or not reported)")
        return {"task_id": task_id, "mode": "historical replay (reconstructed from recorded events; nothing was re-executed)",
                "steps": steps, "complete": not gaps, "gaps": gaps}

    def compare(self, project_id: str, first: str, second: str) -> Dict[str, Any]:
        """Two recorded events' states: files (from checkpoints or change records), tests, measurements."""
        a, b = self.ledger.get(project_id, first), self.ledger.get(project_id, second)
        if a is None or b is None:
            raise KeyError(first if a is None else second)
        out: Dict[str, Any] = {"first": a.model_dump(mode="json"), "second": b.model_dump(mode="json"), "notes": []}
        fa, fb = (a.data.get("files_map") if a.type == "checkpoint_created" else None), \
                 (b.data.get("files_map") if b.type == "checkpoint_created" else None)
        if fa is not None and fb is not None:
            out["files"] = {"added": sorted(set(fb) - set(fa)), "removed": sorted(set(fa) - set(fb)),
                            "modified": sorted(p for p in set(fa) & set(fb) if fa[p] != fb[p])}
        else:
            out["notes"].append("file-level comparison needs two checkpoints; other events only list the files they changed")
        if a.type == b.type == "performance_measured":
            wa, wb = a.config.get("workload"), b.config.get("workload")
            if wa != wb:
                out["notes"].append("the workloads differ: the measurements are not directly comparable")
            out["performance"] = {"first": a.data.get("endpoints"), "second": b.data.get("endpoints")}
        if a.type == b.type == "test_executed":
            out["tests"] = {"first": a.data.get("checks", {}).get("tests"), "second": b.data.get("checks", {}).get("tests")}
            if (a.data.get("checks", {}).get("tests") or {}).get("environment") != (b.data.get("checks", {}).get("tests") or {}).get("environment"):
                out["notes"].append("the tests ran in different environments")
        out["revision_changed"] = a.revision != b.revision
        return out

    # --- checkpoints and restoration ------------------------------------------------------------------------------

    def checkpoint(self, project_id: str, project: Path, user_id: str, name: str, task_id: Optional[str] = None) -> Event:
        files, unstored = st.current_map(project, self.ledger)
        tests = next((e for e in reversed(self.ledger.events(project_id)) if e.type == "test_executed"), None)
        ev = emit(project_id, "checkpoint_created", f"user {user_id}", f"checkpoint '{name}'", "success", task_id=task_id,
                  refs={"checkpoint": name}, project_dir=project, ledger=self.ledger,
                  data={"name": name, "files_map": files, "unstored": unstored, "file_count": len(files),
                        "latest_test_event": tests.id if tests else None,
                        "latest_test_outcome": tests.outcome if tests else None})
        if ev is None:
            raise TimeMachineError("the checkpoint could not be recorded")
        return ev

    def _target_map(self, project_id: str, project: Path, target: Dict[str, str]) -> Dict[str, Any]:
        """The file map a restore aims for: a checkpoint, or the current state with one recorded change reverted."""
        events = self.ledger.events(project_id)
        if target.get("checkpoint_id"):
            cp = next((e for e in events if e.id == target["checkpoint_id"] and e.type == "checkpoint_created"), None)
            if cp is None:
                raise KeyError(target["checkpoint_id"])
            return {"files": dict(cp.data["files_map"]), "label": f"checkpoint '{cp.data.get('name')}'", "event": cp}
        if target.get("revert_change_id"):
            ch = next((e for e in events if e.id == target["revert_change_id"] and e.type in st.CHANGE_TYPES), None)
            if ch is None:
                raise KeyError(target["revert_change_id"])
            current, _ = st.current_map(project, self.ledger)
            prev, conflicts = st.revert(current, ch)
            if prev is None:
                raise TimeMachineError("the change cannot be reverted: these files were modified afterwards: " + ", ".join(conflicts))
            return {"files": prev, "label": f"current state without change {ch.id}", "event": ch}
        raise TimeMachineError("give a checkpoint_id or a revert_change_id")

    def preview(self, project_id: str, project: Path, target: Dict[str, str], user_id: str = "") -> Dict[str, Any]:
        """
        What restoring `target` into the project would do, file by file:
          unchanged   already identical
          restore     the current content was written by a recorded AIForge change (safe to replace)
          conflict    the current content was not produced by any recorded change (user or another session):
                      it is never overwritten
          unavailable the target content was not stored (secret-like values or binary)
        """
        t = self._target_map(project_id, project, target)
        current, _ = st.current_map(project, self.ledger)
        produced: Dict[str, set] = {}
        for ch in st.changes(self.ledger.events(project_id)):
            for f in ch.files:
                produced.setdefault(f["path"], set()).add(f.get("after"))
        rows = []
        for path in sorted(set(current) | set(t["files"])):
            cur, want = current.get(path), t["files"].get(path)
            if cur == want:
                continue
            if want is not None and self.ledger.get_blob(want) is None:
                action, why = "unavailable", "the target content was not stored"
            elif cur in produced.get(path, set()):
                action, why = "restore", "current content was written by a recorded AIForge change"
            else:
                action, why = "conflict", ("not produced by any recorded change (edited by a person or another session); "
                                           "it will not be touched")
            rows.append({"path": path, "action": action, "current": cur, "target": want, "reason": why,
                         "operation": "delete" if want is None else "create" if cur is None else "replace"})
        token = hashlib.sha256(json.dumps({"rev": st.revision_of(current), "target": target, "rows": rows},
                                          sort_keys=True).encode()).hexdigest()
        result = {"target": target, "label": t["label"], "rows": rows, "token": token,
                  "restore": sum(1 for r in rows if r["action"] == "restore"),
                  "conflicts": sum(1 for r in rows if r["action"] == "conflict"),
                  "unavailable": sum(1 for r in rows if r["action"] == "unavailable"),
                  "current_revision": st.revision_of(current), "target_revision": st.revision_of(t["files"])}
        emit(project_id, "restore_previewed", f"user {user_id}" if user_id else "Time Machine",
             f"restore preview: {result['restore']} file(s) to restore, {result['conflicts']} conflict(s)", "info",
             refs={k: v for k, v in target.items()}, ledger=self.ledger, data={k: v for k, v in result.items() if k != "rows"})
        return result

    def restore_isolated(self, project_id: str, project: Path, user_id: str, target: Dict[str, str],
                         run_tests: bool = True) -> Dict[str, Any]:
        """Materialize the target state in a separate folder and run its tests there. The project is not touched."""
        from backend.evolution.autopilot import validation
        t = self._target_map(project_id, project, target)
        folder, missing = st.materialize(t["files"], self.ledger)
        if folder is None:
            raise TimeMachineError("the target cannot be rebuilt: content not stored for " + ", ".join(missing[:10]))
        try:
            tests = validation.check_tests(folder) if run_tests else None
            result = {"label": t["label"], "revision": st.revision_of(t["files"]), "files": len(t["files"]),
                      "tests": tests.model_dump(mode="json") if tests else None,
                      "failing_tests": _failing_tests(tests.output) if tests else []}
        finally:
            shutil.rmtree(folder.parent, ignore_errors=True)
        emit(project_id, "restore_performed", f"user {user_id}", f"isolated restore of {t['label']}: tests "
             f"{result['tests']['status'] if result['tests'] else 'not run'}", "info", refs=dict(target), ledger=self.ledger,
             data={"isolated": True, "revision": result["revision"],
                   "tests": {k: (result["tests"] or {}).get(k) for k in ("status", "counts", "environment")}})
        return result

    def restore(self, project_id: str, project: Path, user_id: str, target: Dict[str, str], token: str,
                approved: bool) -> Dict[str, Any]:
        """Restore into the project: only 'restore' rows, only with approval of the exact preview, after a recovery point."""
        from backend.evolution.autopilot import validation
        from backend.evolution.autopilot.executor import apply_all
        if not approved:
            raise TimeMachineError("restoring into the project changes files: approve it explicitly")
        preview = self.preview(project_id, project, target, user_id)
        if preview["token"] != token:
            raise TimeMachineError("the project or the target changed since the preview: preview again and approve that")
        rows = [r for r in preview["rows"] if r["action"] == "restore"]
        if not rows:
            raise TimeMachineError("nothing can be restored safely (only conflicts or unavailable files)")
        recovery = self.checkpoint(project_id, project, user_id, f"recovery point before restoring {preview['label']}")
        before = {r["path"]: (project / r["path"]).read_bytes().decode("utf-8") if (project / r["path"]).is_file() else None
                  for r in rows}
        writes = {r["path"]: self.ledger.get_blob(r["target"]) for r in rows if r["target"] is not None}
        written, ok = apply_all(project, writes, f"Time Machine restore ({preview['label']})") if writes else ([], True)
        if not ok:
            raise TimeMachineError("the files could not be written; the project is unchanged")
        for r in rows:
            if r["target"] is None and (project / r["path"]).is_file():
                (project / r["path"]).unlink()
        after = {r["path"]: (project / r["path"]).read_bytes().decode("utf-8") if (project / r["path"]).is_file() else None
                 for r in rows}
        from backend.time_machine.recorder import file_records
        tests = validation.check_tests(project)
        ev = emit(project_id, "restore_performed", f"user {user_id}",
                  f"restored {len(rows)} file(s) to {preview['label']}; tests {tests.status}",
                  "success" if tests.status == "passed" else "failure", refs=dict(target), project_dir=project,
                  ledger=self.ledger, parents=[recovery.id], files=file_records(before, after, self.ledger),
                  data={"isolated": False, "recovery_checkpoint": recovery.id, "conflicts_left": preview["conflicts"],
                        "tests": {"status": tests.status, "counts": tests.counts, "environment": tests.environment}})
        return {"restored": [r["path"] for r in rows], "conflicts_left": [r["path"] for r in preview["rows"] if r["action"] == "conflict"],
                "recovery_checkpoint": recovery.id, "event_id": ev.id if ev else None,
                "tests": tests.model_dump(mode="json")}

    # --- jobs (investigations, reruns) ------------------------------------------------------------------------------

    def _start(self, project_id: str, job: Job, target: Callable[[], None]) -> Job:
        with self._lock:
            if project_id in self._active:
                raise Busy(f"another Time Machine job ({self._active[project_id]}) is running for this project")
            self._active[project_id] = job.id
        self.jobs.put(project_id, "jobs", job)

        def run():
            try:
                target()
            finally:
                with self._lock:
                    self._active.pop(project_id, None)
        if self.background:
            threading.Thread(target=run, name=f"timemachine-{job.id}", daemon=True).start()
        else:
            run()
        return self.jobs.get(project_id, "jobs", job.id)

    def cancel(self, project_id: str, job_id: str) -> Optional[Job]:
        def change(j: Job):
            if j.status in ("queued", "running"):
                j.cancel_requested = True
        return self.jobs.update(project_id, "jobs", job_id, change)

    def _step(self, project_id: str, job_id: str, **step) -> None:
        self.jobs.update(project_id, "jobs", job_id, lambda j: j.steps.append({"at": now_iso(), **step}))

    def _stopped(self, project_id: str, job_id: str, deadline: float) -> bool:
        j = self.jobs.get(project_id, "jobs", job_id)
        return bool(j and j.cancel_requested) or time.monotonic() > deadline

    # --- the Regression Detective ------------------------------------------------------------------------------------

    def investigate(self, project_id: str, project: Path, user_id: str) -> Job:
        job = Job(id="tmi_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id, kind="investigation")
        return self._start(project_id, job, lambda: self._investigate(project_id, job.id, Path(project)))

    def _run_tests(self, project_id: str, job_id: str, files: Dict[str, str], label: str, rerun_on_fail: bool = True):
        """Tests of a reconstructed state in an isolated folder. A failure is re-run once (flaky check)."""
        from backend.evolution.autopilot import validation
        folder, missing = st.materialize(files, self.ledger, "state")
        if folder is None:
            self._step(project_id, job_id, state=label, status="unavailable", detail="content not stored: " + ", ".join(missing[:5]))
            return "unavailable", None
        try:
            res = validation.check_tests(folder)
            status = res.status
            if status == "failed" and rerun_on_fail:
                again = validation.check_tests(folder)
                if again.status == "passed":
                    status = "flaky"
            self._step(project_id, job_id, state=label, status=status, revision=st.revision_of(files)[:16],
                       environment=res.environment, counts=res.counts, failing=_failing_tests(res.output),
                       output_tail=redact(res.output[-1200:]))
            return status, res
        finally:
            shutil.rmtree(folder.parent, ignore_errors=True)

    def _investigate(self, project_id: str, job_id: str, project: Path) -> None:
        deadline = time.monotonic() + INVESTIGATION_DEADLINE
        self.jobs.update(project_id, "jobs", job_id, lambda j: setattr(j, "status", "running"))
        result: Dict[str, Any] = {"verdict": "inconclusive", "evidence": [], "limitations": []}
        runs = 0
        try:
            events = self.ledger.events(project_id)
            current, unstored = st.current_map(project, self.ledger)
            if unstored:
                result["limitations"].append(f"{len(unstored)} file(s) could not be stored (secret-like or binary): "
                                             + ", ".join(unstored[:5]))
            status, res = self._run_tests(project_id, job_id, current, "current project")
            runs += 1
            result["current"] = {"status": status, "failing": _failing_tests(res.output) if res else []}
            if status != "failed":
                result["verdict"] = "not_reproduced"
                result["summary"] = (f"the project's tests are '{status}' now; no failure to investigate"
                                     if status != "flaky" else "the failure is not reproducible (the tests passed on a re-run)")
                return
            ch = st.chain(current, events)
            states = ch["states"]                                            # newest first
            if ch["stopped"]:
                result["limitations"].append(ch["stopped"]["reason"] + f" ({', '.join(ch['stopped']['conflicts'])})")
            passing = {e.revision: e for e in events if e.type == "test_executed" and e.outcome == "success" and e.revision}
            good_index = next((i for i, s_ in enumerate(states) if s_["revision"] in passing), None)
            if good_index is not None:
                result["known_good"] = {"revision": states[good_index]["revision"], "how": "recorded passing test run",
                                        "event": passing[states[good_index]["revision"]].id}
            elif len(states) > 1:
                good_index = len(states) - 1
                result["known_good"] = {"revision": states[good_index]["revision"], "how": "oldest reconstructable state "
                                        "(no recorded passing test for it): checked by running its tests now"}
            else:
                result["summary"] = "no recorded change can be reverted, so there is no earlier state to compare with"
                return
            if self._stopped(project_id, job_id, deadline):
                raise InterruptedError("cancelled")
            g_status, _ = self._run_tests(project_id, job_id, states[good_index]["files"], "known-good state")
            runs += 1
            if g_status != "passed":
                result["summary"] = (f"the known-good state does not pass its tests here ({g_status}): the failure may come "
                                     "from the environment or dependencies, not from a recorded change")
                result["limitations"].append("the environment differs from when the passing run was recorded")
                return
            # recorded changes between known-good and now, oldest first
            between = list(reversed(states[:good_index]))                   # states after each change, oldest first
            change_ids = [s_["after_change"] for s_ in between]                # the change that produced each state
            by_id = {e.id: e for e in events}
            result["changes"] = [{"id": c, "summary": by_id[c].summary, "source": by_id[c].source, "at": by_id[c].at,
                                  "files": [f["path"] for f in by_id[c].files], "task_id": by_id[c].task_id}
                                 for c in change_ids]
            # binary search for the first state that fails (cumulative application from known-good)
            lo, hi = 0, len(between) - 1                                    # between[hi] is the current state (fails)
            statuses: Dict[int, str] = {hi: "failed"}
            while lo < hi and runs < MAX_BISECT_RUNS:
                if self._stopped(project_id, job_id, deadline):
                    raise InterruptedError("cancelled")
                mid = (lo + hi) // 2
                s_status, _ = self._run_tests(project_id, job_id, between[mid]["files"], f"after change {mid + 1} of {len(between)}")
                runs += 1
                statuses[mid] = s_status
                if s_status == "failed":
                    hi = mid
                elif s_status == "passed":
                    lo = mid + 1
                else:
                    result["limitations"].append(f"a state could not be judged ({s_status}); the search stopped")
                    break
            first_bad = hi
            search_complete = lo == hi
            if not search_complete:
                result["limitations"].append(f"the search stopped after {runs} test runs: the cause is among changes "
                                             f"{lo + 1}..{hi + 1} of {len(between)}")
            suspect = by_id[change_ids[first_bad]]
            result["suspect"] = {"change": suspect.id, "summary": suspect.summary, "files": [f["path"] for f in suspect.files],
                                 "task_id": suspect.task_id, "source": suspect.source}
            result["evidence"].append(f"tests pass at the known-good state and fail from the state after change "
                                      f"{suspect.id} ({suspect.summary}) onwards")
            # isolation: the change alone on top of known-good, and the current state without it
            alone, _ = st.apply(states[good_index]["files"], suspect)
            alone_status = without_status = None
            if alone is not None and first_bad > 0:
                alone_status, _ = self._run_tests(project_id, job_id, alone, "known-good + only the suspected change")
                runs += 1
            elif first_bad == 0:
                alone_status = "failed"                                       # it is the first change: same state as tested
            without, conflicts = st.revert(current, suspect)
            if without is not None:
                without_status, _ = self._run_tests(project_id, job_id, without, "current state without the suspected change")
                runs += 1
                result["proposal"] = {"kind": "revert_change", "revert_change_id": suspect.id,
                                      "tests_after_revert": without_status,
                                      "how": "preview and approve a restore with this revert_change_id (only files written by "
                                             "that change are touched)"}
            else:
                result["limitations"].append("the suspected change cannot be reverted alone: " + ", ".join(conflicts))
            if alone_status is None:
                result["limitations"].append("the change cannot be applied alone on the known-good state (an earlier change "
                                             "touched the same file); isolation relies on reverting it from the current state")
            if not search_complete:
                result["verdict"] = "hypothesis"
            elif without_status == "passed" and alone_status in ("failed", None):
                # an exact pass -> fail transition across this change, and reverting only this change fixes it
                result["verdict"] = "confirmed"
                result["evidence"].append("reverting only this change makes the failing tests pass"
                                          + ("; applied alone on the known-good state it makes them fail" if alone_status else ""))
            elif without_status == "passed" or alone_status == "failed":
                result["verdict"] = "probable"
                result["evidence"].append(f"isolation: change alone -> {alone_status}; current without it -> {without_status}")
            else:
                result["verdict"] = "hypothesis"
                result["evidence"].append(f"the transition was found, but isolation did not confirm it (change alone -> "
                                          f"{alone_status}; current without it -> {without_status}): changes may interact")
        except InterruptedError:
            self.jobs.update(project_id, "jobs", job_id, lambda j: setattr(j, "status", "cancelled"))
            result["verdict"] = "inconclusive"
            result["summary"] = "cancelled"
        except Exception as e:  # noqa: BLE001
            _logger.exception("Time Machine investigation %s failed", job_id)
            result["verdict"] = "inconclusive"
            result["error"] = redact(f"{type(e).__name__}: {e}", 800)
        finally:
            result["test_runs"] = runs

            def done(j: Job):
                j.result = result
                if j.status == "running":
                    j.status = "failed" if result.get("error") else "completed"
                j.finished_at = now_iso()
            self.jobs.update(project_id, "jobs", job_id, done)
            emit(project_id, "investigation_completed", "Time Machine",
                 f"regression investigation: {result['verdict']}" + (f" - {result['suspect']['summary']}" if result.get("suspect") else ""),
                 {"confirmed": "success", "probable": "info", "not_reproduced": "info"}.get(result["verdict"], "inconclusive"),
                 task_id=job_id, refs={"job_id": job_id, **({"suspect": result["suspect"]["change"]} if result.get("suspect") else {})},
                 parents=[result["suspect"]["change"]] if result.get("suspect") else [], project_dir=project,
                 ledger=self.ledger, data={k: v for k, v in result.items() if k in ("verdict", "known_good", "evidence", "test_runs")})

    # --- experimental rerun ------------------------------------------------------------------------------------------

    def rerun(self, project_id: str, project: Path, user_id: str, execution_id: str,
              generate: Optional[Callable[[str, str], str]] = None) -> Job:
        """Run a recorded Autopilot execution's plan again, in isolation, at the revision it started from."""
        job = Job(id="tmr_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id, kind="rerun",
                  target={"execution_id": execution_id})
        return self._start(project_id, job, lambda: self._rerun(project_id, job.id, Path(project), execution_id, generate))

    def _rerun(self, project_id: str, job_id: str, project: Path, execution_id: str, generate) -> None:
        from backend.evolution.autopilot.service import AutopilotService, global_autopilot_service
        from backend.evolution.autopilot.store import AutopilotStore
        self.jobs.update(project_id, "jobs", job_id, lambda j: setattr(j, "status", "running"))
        result: Dict[str, Any] = {"mode": "experimental rerun (executed again now; NOT a reproduction of the original)",
                                  "differences": [], "limitations": []}
        tmp = None
        try:
            events = self.ledger.events(project_id)
            started = next((e for e in events if e.type == "agent_started" and e.refs.get("execution_id") == execution_id), None)
            applied = next((e for e in events if e.type == "patch_applied" and e.refs.get("execution_id") == execution_id), None)
            recorded_after = next((e for e in events if e.type == "test_executed" and e.refs.get("execution_id") == execution_id
                                   and "after" in e.data.get("phase", "")), None)
            if started is None:
                raise TimeMachineError("the execution's start was not recorded, so its starting revision is unknown")
            plan = global_autopilot_service.store.get(project_id, "plans", started.refs.get("plan_id", ""))
            if plan is None:
                raise TimeMachineError("the plan of that execution is no longer stored")
            current, _ = st.current_map(project, self.ledger)
            ch = st.chain(current, events)
            match = next((s_ for s_ in ch["states"] if s_["revision"] == started.revision), None)
            if match is None:
                raise TimeMachineError("the starting revision cannot be reconstructed from the recorded changes"
                                       + (f": {ch['stopped']['reason']}" if ch["stopped"] else ""))
            folder, missing = st.materialize(match["files"], self.ledger, "rerun")
            if folder is None:
                raise TimeMachineError("content not stored for " + ", ".join(missing[:5]))
            tmp = folder.parent
            ap = AutopilotService(AutopilotStore(tmp / "autopilot"), background=False)
            copy = plan.model_copy(deep=True)
            copy.status = copy.status.__class__("approved")
            # the rerun's own events go to a separate history: they must never look like changes to the project
            rerun_id = f"rerun-{job_id}"
            copy.project_id = rerun_id
            ap.store.put(rerun_id, "plans", copy)
            from backend.evolution.autopilot.executor import execution_config
            current_config = execution_config(True, generate)
            ex = ap.execute(rerun_id, copy.id, "time-machine-rerun", folder, generate=generate, include_tests=True)
            result["rerun_history"] = rerun_id
            new_files = {r: (folder / r).read_bytes().decode("utf-8") if (folder / r).is_file() else None for r in ex.changed_files}
            recorded = {f["path"]: f.get("after") for f in (applied.files if applied else [])}
            per_file = []
            for path in sorted(set(recorded) | set(new_files)):
                new_sha = hashlib.sha256(new_files[path].encode()).hexdigest() if new_files.get(path) is not None else None
                per_file.append({"path": path, "recorded_after": recorded.get(path), "rerun_after": new_sha,
                                 "identical": recorded.get(path) == new_sha and path in recorded})
            tests_new = next((c for c in ex.after if c.check_id == "tests"), None)
            tests_old = (recorded_after.data.get("checks", {}).get("tests") if recorded_after else None)
            result.update({
                "start_revision": started.revision, "rerun_status": ex.status, "applied_in_isolation": ex.applied_to_project,
                "files": per_file, "identical_output": bool(per_file) and all(f["identical"] for f in per_file),
                "tests": {"recorded": tests_old, "rerun": {"status": tests_new.status, "counts": tests_new.counts,
                                                           "environment": tests_new.environment} if tests_new else None},
                "configuration": {"recorded": started.config, "now": current_config}})
            changed = sorted(k for k in set(started.config) | set(current_config) if started.config.get(k) != current_config.get(k))
            if changed:
                result["differences"].append("configuration differs from the recorded one: " + ", ".join(changed))
            if tests_old and tests_new and tests_old.get("environment") != tests_new.environment:
                result["differences"].append(f"test environment: {tests_old.get('environment')} -> {tests_new.environment}")
            if applied is None:
                result["limitations"].append("the original execution applied nothing, so there is no recorded output to compare")
        except Exception as e:  # noqa: BLE001
            result["error"] = redact(f"{type(e).__name__}: {e}", 800)
        finally:
            if tmp is not None:
                shutil.rmtree(tmp, ignore_errors=True)

            def done(j: Job):
                j.result = result
                j.status = "failed" if result.get("error") else "completed"
                j.finished_at = now_iso()
            self.jobs.update(project_id, "jobs", job_id, done)
            emit(project_id, "rerun_completed", "Time Machine",
                 f"experimental rerun of {execution_id}: " + ("error" if result.get("error") else
                                                              "identical output" if result.get("identical_output") else "output differs"),
                 "error" if result.get("error") else "info", task_id=job_id, refs={"job_id": job_id, "execution_id": execution_id},
                 parent_ref=("execution_id", execution_id), ledger=self.ledger,
                 data={k: v for k, v in result.items() if k in ("identical_output", "differences", "rerun_status", "error")})

    def rerun_experiment(self, project_id: str, project: Path, user_id: str, experiment_id: str,
                         generate: Optional[Callable[[str, str], str]] = None) -> Job:
        """Run a recorded Evolution experiment's plan again, in isolation, at its source revision."""
        job = Job(id="tmr_" + uuid.uuid4().hex[:12], project_id=project_id, user_id=user_id, kind="rerun",
                  target={"experiment_id": experiment_id})
        return self._start(project_id, job, lambda: self._rerun_experiment(project_id, job.id, Path(project), experiment_id, generate))

    def _rerun_experiment(self, project_id: str, job_id: str, project: Path, experiment_id: str, generate) -> None:
        from backend.evolution.autopilot.service import AutopilotService
        from backend.evolution.autopilot.store import AutopilotStore
        from backend.evolution_engine.service import EvolutionEngine, EvolutionStore, global_evolution_engine
        self.jobs.update(project_id, "jobs", job_id, lambda j: setattr(j, "status", "running"))
        result: Dict[str, Any] = {"mode": "experimental rerun (executed again now; NOT a reproduction of the original)",
                                  "differences": [], "limitations": []}
        tmp = None
        try:
            original = global_evolution_engine.store.get(project_id, "experiments", experiment_id)
            if original is None or not original.source_revision:
                raise TimeMachineError("the experiment or its source revision is not stored")
            current, _ = st.current_map(project, self.ledger)
            ch = st.chain(current, self.ledger.events(project_id))
            match = next((s_ for s_ in ch["states"] if s_["revision"] == original.source_revision), None)
            if match is None:
                raise TimeMachineError("the experiment's source revision cannot be reconstructed from the recorded changes")
            folder, missing = st.materialize(match["files"], self.ledger, "rerun")
            if folder is None:
                raise TimeMachineError("content not stored for " + ", ".join(missing[:5]))
            tmp = folder.parent
            rerun_id = f"rerun-{job_id}"
            engine = EvolutionEngine(EvolutionStore(tmp / "evolution"), autopilot=AutopilotService(AutopilotStore(tmp / "ap"),
                                     background=False), background=False, generate=generate)
            op = original.opportunity.model_copy(deep=True)
            op.project_id, op.history = rerun_id, []
            engine.store.put(rerun_id, "opportunities", op)
            exp = engine.create_experiment(rerun_id, folder, "time-machine-rerun", op.id, len(original.plan.strategies),
                                           original.plan.weights, original.plan.thresholds, workload=original.plan.workload)
            engine.run(rerun_id, folder, "time-machine-rerun", exp.id, approved=True)
            new = engine.store.get(rerun_id, "experiments", exp.id)
            old_c = {c.strategy: c for c in original.candidates}
            rows = []
            for c in new.candidates:
                o = old_c.get(c.strategy)
                rows.append({"strategy": c.strategy, "recorded": {"patch_hash": o.patch_hash, "eligible": o.eligible,
                                                                  "performance": o.performance.get("decision")} if o else None,
                             "rerun": {"patch_hash": c.patch_hash, "eligible": c.eligible, "performance": c.performance.get("decision")},
                             "identical_patch": bool(o and o.patch_hash and o.patch_hash == c.patch_hash)})
            result.update({"start_revision": original.source_revision, "recorded_outcome": original.outcome,
                           "rerun_outcome": new.outcome, "recorded_selected": original.selected, "rerun_selected": new.selected,
                           "candidates": rows, "rerun_history": rerun_id,
                           "configuration": {"recorded": {c.id: c.model for c in original.candidates},
                                             "now": {c.id: c.model for c in new.candidates}}})
            if original.outcome != new.outcome:
                result["differences"].append(f"outcome {original.outcome} -> {new.outcome}")
            if any(not r["identical_patch"] for r in rows):
                result["differences"].append("at least one candidate's code differs from the recorded one")
            result["limitations"].append("measurements depend on the machine's load at the time; compare them as runs, not as proof")
        except Exception as e:  # noqa: BLE001
            result["error"] = redact(f"{type(e).__name__}: {e}", 800)
        finally:
            if tmp is not None:
                shutil.rmtree(tmp, ignore_errors=True)

            def done(j: Job):
                j.result = result
                j.status = "failed" if result.get("error") else "completed"
                j.finished_at = now_iso()
            self.jobs.update(project_id, "jobs", job_id, done)
            emit(project_id, "rerun_completed", "Time Machine", f"experimental rerun of experiment {experiment_id}: "
                 + ("error" if result.get("error") else f"{result.get('recorded_outcome')} -> {result.get('rerun_outcome')}"),
                 "error" if result.get("error") else "info", task_id=job_id,
                 refs={"job_id": job_id, "experiment_id": experiment_id}, ledger=self.ledger,
                 data={k: v for k, v in result.items() if k in ("differences", "rerun_outcome", "recorded_outcome", "error")})


global_time_machine = TimeMachine()
