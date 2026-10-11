"""
Executes an approved plan:

  1. copy the project to an isolated workspace and record content hashes of the original
  2. run the baseline checks on the untouched copy
  3. apply each task in the copy (deterministic fixers or the coding model), within the plan's
     file scope, with bounded retries and cancellation points
  4. run the same checks again and compare them with the baseline
  5. accepted -> write the changed files to the project (refused if any of them changed meanwhile);
     rejected -> the copy is discarded and the project is untouched
  6. analyze the project again: a finding is verified only if it is no longer detected
"""

import difflib
import logging
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from backend.evolution.autopilot import validation
from backend.evolution.autopilot.models import (Execution, FindingStatus, Plan, PlanStatus, Stage, TaskResult,
                                                now_iso)
from backend.evolution.autopilot.plans import TEST_DIR, scope_violations
from backend.evolution.autopilot.redact import redact
from backend.evolution.autopilot.workspace import (create_workspace, discard_workspace, file_hash,
                                                   WorkspaceError)

_logger = logging.getLogger("aiforge.autopilot.executor")

STAGES = ["prepare workspace", "baseline checks", "implement", "after checks", "compare", "apply", "re-analyze"]
EXECUTION_DEADLINE_SECONDS = 45 * 60
MODEL_ATTEMPTS = 2
DIFF_LIMIT = 120_000
AUTOPILOT_SYSTEM_PROMPT = (
    "You are a senior engineer fixing specific, reported problems in an existing project. Fix only the "
    "listed problems and keep all other behaviour unchanged. Never delete tests, weaken assertions or "
    "add placeholder code to make checks pass. Return each changed or new file in full as a `### <path>` "
    "line followed by one fenced code block. Do not return unchanged files."
)


class Cancelled(Exception):
    pass


def apply_all(root: Path, changes: Dict[str, Optional[str]], reason: str) -> Tuple[List[str], bool]:
    """
    The patch engine's atomic apply (path validation, rollback), in batches of its file limit;
    a failing batch rolls back the batches already written, so the result is all or nothing.
    """
    from backend.repository.patch_engine import MAX_FILES_PER_CHANGE, global_patch_engine
    root = Path(root)
    items = list(changes.items())
    written: List[str] = []
    undo: Dict[str, Optional[str]] = {}
    for i in range(0, len(items), MAX_FILES_PER_CHANGE):
        batch = dict(items[i:i + MAX_FILES_PER_CHANGE])
        for rel in batch:
            try:
                undo[rel] = (root / rel).read_text(encoding="utf-8") if (root / rel).is_file() else None
            except (OSError, UnicodeDecodeError):
                undo[rel] = None
        applied, ok = global_patch_engine.apply_changes(str(root), batch, reason=reason)
        if not ok:
            if written:
                rollback = {rel: undo[rel] for rel in written}
                for j in range(0, len(rollback), MAX_FILES_PER_CHANGE):
                    global_patch_engine.apply_changes(str(root), dict(list(rollback.items())[j:j + MAX_FILES_PER_CHANGE]),
                                                      reason="roll back " + reason)
            return [], False
        written += applied
    return written, True


class _Run:
    def __init__(self, store, execution: Execution, plan: Plan, project: Path, generate, include_tests: bool):
        self.store, self.plan, self.project = store, plan, project
        self.execution_id, self.project_id = execution.id, execution.project_id
        self.generate, self.include_tests = generate, include_tests
        self.deadline = time.monotonic() + EXECUTION_DEADLINE_SECONDS
        self.workspace: Optional[Path] = None
        self.changes: Dict[str, Optional[str]] = {}       # path -> new content in the workspace (None = deleted)
        self.original: Dict[str, Optional[str]] = {}      # path -> original content (None = new file)
        self.original_hash: Dict[str, Optional[str]] = {} # path -> sha256 of the original bytes

    # --- bookkeeping -----------------------------------------------------------------------

    def save(self, change: Callable[[Execution], None]) -> Execution:
        return self.store.update(self.project_id, "executions", self.execution_id, change)

    def stage(self, name: str, status: str, detail: str = "") -> None:
        def change(e: Execution):
            for s in e.stages:
                if s.name == name:
                    s.status, s.at, s.detail = status, now_iso(), redact(detail, 2000)
        self.save(change)

    def checkpoint(self) -> None:
        current = self.store.get(self.project_id, "executions", self.execution_id)
        if current is not None and current.cancel_requested:
            raise Cancelled()
        if time.monotonic() > self.deadline:
            raise TimeoutError(f"execution exceeded {EXECUTION_DEADLINE_SECONDS // 60} minutes")

    # --- workspace helpers --------------------------------------------------------------------

    def read(self, rel: str) -> Optional[str]:
        try:
            return (self.workspace / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None

    def write_changes(self, changes: Dict[str, Optional[str]], reason: str) -> List[str]:
        for rel in changes:
            if rel not in self.original:
                # The workspace still holds the project as it was copied at the start.
                self.original[rel] = self.read(rel)
                self.original_hash[rel] = file_hash(self.workspace / rel)
        applied, ok = apply_all(self.workspace, changes, reason)
        if not ok:
            raise RuntimeError("the patch could not be applied to the working copy")
        for rel in applied:
            self.changes[rel] = self.read(rel) if (self.workspace / rel).exists() else None
        return applied

    # --- task strategies --------------------------------------------------------------------------

    def fix_ruff(self, files: List[str]) -> Dict[str, Optional[str]]:
        targets = [f for f in files if f.endswith(".py") and (self.workspace / f).is_file()]
        if not targets:
            return {}
        before = {f: self.read(f) for f in targets}
        subprocess.run([sys.executable, "-m", "ruff", "check", "--select", "F401", "--fix", "--no-cache",
                        *[str(self.workspace / f) for f in targets]], capture_output=True, text=True, timeout=120)
        after = {f: self.read(f) for f in targets}
        for f, content in before.items():                     # re-applied through the patch engine below
            (self.workspace / f).write_text(content, encoding="utf-8")
        return {f: after[f] for f in targets if after[f] is not None and after[f] != before[f]}

    def fix_requirements(self, findings) -> Dict[str, Optional[str]]:
        packages = sorted({m.group(1) for f in findings for m in [re.search(r"'([^']+)'", f.title)] if m})
        current = self.read("requirements.txt") or ""
        declared = {re.split(r"[<>=!~\[;\s]", line.strip())[0].lower() for line in current.splitlines() if line.strip()}
        missing = [p for p in packages if p.split("[")[0].lower() not in declared]
        if not missing:
            return {}
        text = current if not current or current.endswith("\n") else current + "\n"
        return {"requirements.txt": text + "\n".join(missing) + "\n"}

    def fix_imports(self, files: List[str]) -> Dict[str, Optional[str]]:
        from backend.agents.repair_strategies import fix_misplaced_imports, fix_shadowed_module, fix_undefined_names
        from backend.routes.export import _read_project_dir
        from backend.validation.quality_gate import run_quality_gate
        gate = run_quality_gate(self.workspace)
        errors = [e for e in gate.get("errors", []) if e.get("file") in files]
        if not errors:
            return {}
        sources = _read_project_dir(self.workspace)
        changes: Dict[str, Optional[str]] = {}
        for strategy in (lambda s: fix_undefined_names(s, errors), lambda s: fix_misplaced_imports(s, errors),
                         lambda s: fix_shadowed_module(s, errors)):
            for rel, content in strategy({**sources, **{k: v for k, v in changes.items() if v is not None}}).items():
                if content != sources.get(rel):
                    changes[rel] = content
        return changes

    def fix_with_model(self, task, findings, feedback: str = "") -> Dict[str, Optional[str]]:
        from backend.generation.project_editor import propose_changes, relevant_files
        from backend.routes.export import _read_project_dir
        files = _read_project_dir(self.workspace)
        context = [f for f in task.files if f in files]
        context += [f for f in task.context_files if f in files and f not in context]
        if TEST_DIR in task.files or not context:
            context = (context + relevant_files(self.workspace, task.request or task.title, files, limit=4))[:6]
        context = context[:8]
        leaked = [f for f in context if redact(files[f]) != files[f]]
        if leaked:
            raise PermissionError("not sent to the model: secret-like values in " + ", ".join(leaked))
        allowed = ", ".join(task.files) + (" (new files may be created inside the listed folders)"
                                           if any(f.endswith("/") for f in task.files) else "")
        if task.request:
            request = f"{task.request}\n\nYou may change only: {allowed}"
        else:
            problems = "\n".join(f"- {f.title} ({f.file or 'project'}{':' + str(f.line_start) if f.line_start else ''})\n"
                                 f"  evidence: {f.evidence[:400]}\n  expected fix: {f.remediation}" for f in findings)
            request = f"Fix these reported problems:\n{problems}\n\nYou may change only: {allowed}"
        if feedback:
            request += f"\n\nThe previous attempt was rejected: {feedback}"
        changes, rejected = propose_changes(self.workspace, request, files, context, self.project_id,
                                            self.generate, AUTOPILOT_SYSTEM_PROMPT)
        if rejected:
            _logger.info("Autopilot: model proposed rejected paths %s", rejected)
        # Code blocks lose the final newline; keep files ending the way they did (new files end with one).
        return {p: c if c.endswith("\n") or (files.get(p) is not None and not files[p].endswith("\n")) else c + "\n"
                for p, c in changes.items()}

    # --- the run ---------------------------------------------------------------------------------------

    def implement(self) -> None:
        all_findings = {f.id: f for f in self.store.list(self.project_id, "findings")}
        results: Dict[str, TaskResult] = {}
        for task in self.plan.tasks:
            self.checkpoint()
            findings = [all_findings[i] for i in task.finding_ids if i in all_findings]
            if any(results.get(d) and results[d].status not in ("applied", "no_changes") for d in task.depends_on):
                results[task.id] = TaskResult(task_id=task.id, status="skipped", detail="a task it depends on failed")
            elif task.strategy == "manual":
                results[task.id] = TaskResult(task_id=task.id, status="skipped",
                                              detail="no safe automatic fix; needs a person")
            else:
                results[task.id] = self.run_task(task, findings)
            self.save(lambda e: setattr(e, "task_results", list(results.values())))

    def run_task(self, task, findings) -> TaskResult:
        feedback, attempts = "", 0
        max_attempts = MODEL_ATTEMPTS if task.strategy == "model" else 1
        while attempts < max_attempts:
            attempts += 1
            self.checkpoint()
            try:
                if task.strategy == "ruff_fix":
                    changes = self.fix_ruff(task.files)
                elif task.strategy == "add_requirements":
                    changes = self.fix_requirements(findings)
                elif task.strategy == "import_repair":
                    changes = self.fix_imports(task.files)
                else:
                    changes = self.fix_with_model(task, findings, feedback)
            except (PermissionError, ValueError) as e:
                return TaskResult(task_id=task.id, status="failed", detail=redact(str(e), 500), attempts=attempts)
            except Exception as e:  # noqa: BLE001 - the model or a fixer failed; recorded, other tasks go on
                _logger.warning("Autopilot task %s failed: %s", task.id, e)
                return TaskResult(task_id=task.id, status="failed", detail=redact(f"{type(e).__name__}: {e}", 500),
                                  attempts=attempts)
            if not changes:
                feedback = "no change was proposed"
                continue
            outside = scope_violations(self.plan, list(changes))
            if outside:
                return TaskResult(task_id=task.id, status="out_of_scope", files=sorted(changes), outside=outside, attempts=attempts,
                                  detail="the change touches files the plan did not list")
            syntax_before = self.syntax_errors(list(changes))
            snapshot = {rel: self.read(rel) for rel in changes}
            self.write_changes(changes, reason=f"autopilot {self.plan.id} {task.id}")
            new_errors = [e for e in self.syntax_errors(list(changes)) if e not in syntax_before]
            if new_errors:
                self.revert(snapshot)
                feedback = "it introduced syntax errors: " + "; ".join(new_errors[:3])
                continue
            return TaskResult(task_id=task.id, status="applied", files=sorted(changes), attempts=attempts)
        return TaskResult(task_id=task.id, status="no_changes" if feedback == "no change was proposed" else "failed",
                          detail=feedback, attempts=attempts)

    def revert(self, snapshot: Dict[str, Optional[str]]) -> None:
        apply_all(self.workspace, snapshot, "autopilot revert attempt")
        for rel, content in snapshot.items():
            if self.original.get(rel) == content:
                self.changes.pop(rel, None)
            else:
                self.changes[rel] = content

    def syntax_errors(self, files: List[str]) -> List[str]:
        import ast
        errors = []
        for rel in files:
            if rel.endswith(".py"):
                source = self.read(rel)
                if source is None:
                    continue
                try:
                    ast.parse(source)
                except SyntaxError as e:
                    errors.append(f"{rel}:{e.lineno}: {e.msg}")
        return errors

    def diff(self) -> str:
        chunks = []
        for rel in sorted(self.changes):
            before = (self.original.get(rel) or "").splitlines(keepends=True)
            after = (self.changes[rel] or "").splitlines(keepends=True)
            chunks.append("".join(difflib.unified_diff(before, after, f"a/{rel}", f"b/{rel}")))
        return redact("\n".join(chunks), DIFF_LIMIT)


def run_execution(store, execution_id: str, project_id: str, project_dir: Path,
                  generate: Optional[Callable[[str, str], str]] = None, include_tests: bool = True) -> Execution:
    from backend.evolution.autopilot.service import reanalyze_after_execution
    execution: Execution = store.get(project_id, "executions", execution_id)
    plan: Plan = store.get(project_id, "plans", execution.plan_id)
    project = Path(project_dir).resolve()
    run = _Run(store, execution, plan, project, generate, include_tests)

    def finish(status: str, error: Optional[str] = None, plan_status: Optional[PlanStatus] = None):
        def change(e: Execution):
            e.status, e.finished_at = status, now_iso()
            if error:
                e.error = redact(error, 2000)
        run.save(change)
        if plan_status is not None:
            store.update(project_id, "plans", plan.id, lambda p: setattr(p, "status", plan_status))

    try:
        if plan.status != PlanStatus.APPROVED:
            finish("failed", f"plan is '{plan.status.value}', not approved")
            return store.get(project_id, "executions", execution_id)
        store.update(project_id, "plans", plan.id, lambda p: setattr(p, "status", PlanStatus.RUNNING))

        def started(e: Execution):
            e.status, e.started_at = "running", now_iso()
            e.stages = [Stage(name=n) for n in STAGES]
        run.save(started)

        run.stage("prepare workspace", "running")
        try:
            run.workspace = create_workspace(project)
        except (WorkspaceError, OSError) as e:
            run.stage("prepare workspace", "failed", str(e))
            finish("failed", f"could not create the working copy: {e}", PlanStatus.FAILED)
            return store.get(project_id, "executions", execution_id)
        run.stage("prepare workspace", "done", "isolated copy created (dependency and cache folders left out)")
        run.checkpoint()

        run.stage("baseline checks", "running")
        baseline = validation.run_checks(run.workspace, include_tests=include_tests)
        run.save(lambda e: setattr(e, "baseline", baseline))
        run.stage("baseline checks", "done", ", ".join(f"{c.check_id}: {c.status}" for c in baseline))
        run.checkpoint()

        run.stage("implement", "running")
        run.implement()
        current = store.get(project_id, "executions", execution_id)
        out_of_scope = [r for r in current.task_results if r.status == "out_of_scope"]
        applied = [r for r in current.task_results if r.status == "applied"]
        summary = ", ".join(f"{r.task_id}: {r.status}" for r in current.task_results)
        if out_of_scope:
            files = sorted({f for r in out_of_scope for f in (r.outside or r.files)})
            run.stage("implement", "failed", "needs approval for files outside the plan: " + ", ".join(files))
            run.save(lambda e: (setattr(e, "changed_files", sorted(run.changes)), setattr(e, "diff", run.diff())))
            finish("needs_approval", "the changes touch files the plan did not list: " + ", ".join(files)
                   + ". Approve the plan again with these files to allow them; nothing was applied.",
                   PlanStatus.AWAITING_APPROVAL)
            return store.get(project_id, "executions", execution_id)
        run.stage("implement", "done" if applied else "failed", summary)
        if not run.changes:
            for name in ("after checks", "compare", "apply", "re-analyze"):
                run.stage(name, "skipped", "no changes were made")
            store.set_finding_status(project_id, plan.finding_ids, FindingStatus.FIX_FAILED.value)
            finish("failed", "no task produced a change", PlanStatus.FAILED)
            return store.get(project_id, "executions", execution_id)
        run.save(lambda e: (setattr(e, "changed_files", sorted(run.changes)), setattr(e, "diff", run.diff())))
        run.checkpoint()

        run.stage("after checks", "running")
        after = validation.run_checks(run.workspace, include_tests=include_tests)
        run.save(lambda e: setattr(e, "after", after))
        run.stage("after checks", "done", ", ".join(f"{c.check_id}: {c.status}" for c in after))

        run.stage("compare", "running")
        verdict = validation.compare(baseline, after)
        run.save(lambda e: setattr(e, "verdict", verdict))
        run.stage("compare", "done" if verdict["accepted"] else "failed",
                  "accepted" if verdict["accepted"] else "; ".join(verdict["regressions"] + verdict["unverified"]))
        if not verdict["accepted"]:
            for name in ("apply", "re-analyze"):
                run.stage(name, "skipped", "changes rejected; the project was not modified")
            store.set_finding_status(project_id, plan.finding_ids, FindingStatus.FIX_FAILED.value)
            finish("rejected", "; ".join(verdict["regressions"] + verdict["unverified"]), PlanStatus.FAILED)
            return store.get(project_id, "executions", execution_id)
        run.checkpoint()

        run.stage("apply", "running")
        conflicts = [rel for rel in run.changes if file_hash(project / rel) != run.original_hash.get(rel)]
        if conflicts:
            run.stage("apply", "failed", "changed in the project meanwhile: " + ", ".join(conflicts))
            run.stage("re-analyze", "skipped")
            finish("failed", "the project changed while Autopilot was working (" + ", ".join(conflicts)
                   + "); nothing was overwritten. Run the plan again.", PlanStatus.FAILED)
            return store.get(project_id, "executions", execution_id)
        written, ok = apply_all(project, dict(run.changes), f"AIForge Autopilot plan {plan.id}")
        if not ok:
            run.stage("apply", "failed", "the patch could not be written; the project is unchanged")
            finish("failed", "the patch could not be written to the project", PlanStatus.FAILED)
            return store.get(project_id, "executions", execution_id)
        run.save(lambda e: setattr(e, "applied_to_project", True))
        run.stage("apply", "done", f"{len(written)} file(s) written")

        run.stage("re-analyze", "running")
        tests_passed = any(c.check_id == "tests" and c.status == "passed" for c in after)
        verified, unresolved = reanalyze_after_execution(store, project_id, project, plan.finding_ids, tests_passed)

        def done(e: Execution):
            e.verified_findings, e.unresolved_findings = verified, unresolved
        run.save(done)
        run.stage("re-analyze", "done", f"{len(verified)} verified, {len(unresolved)} still detected")
        finish("completed", None, PlanStatus.COMPLETED)
    except Cancelled:
        finish("cancelled", "cancelled by the user; the project was not modified", PlanStatus.CANCELLED)
    except TimeoutError as e:
        finish("failed", str(e), PlanStatus.FAILED)
    except Exception as e:  # noqa: BLE001 - reported on the execution record
        _logger.exception("Autopilot execution %s failed", execution_id)
        finish("failed", f"{type(e).__name__}: {e}", PlanStatus.FAILED)
    finally:
        discard_workspace(run.workspace)
    return store.get(project_id, "executions", execution_id)
