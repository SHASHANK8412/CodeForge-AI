"""
Edit an existing generated project with a follow-up request, changing only what is needed.

  1. retrieve the relevant files (repository index -> impact analysis -> retriever) and the
     project's recorded decisions (project memory)
  2. ask the coding model for the changed or new files only
  3. validate every path (inside the project, no excluded/secret files, a bounded number)
  4. measure the quality gate and tests before, apply the patch atomically, measure again
  5. roll back automatically when the edit adds blocking errors or breaks passing tests

The old "modify" path re-ran the whole generation, which replaced the project. Generated code
runs only under the sandbox policy (backend/execution/docker_test_sandbox.py).
"""

import logging
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

_logger = logging.getLogger("aiforge.generation.project_editor")

MAX_CHANGED_FILES = 8
MAX_CONTEXT_CHARS = 12_000

SYSTEM_PROMPT = (
    "You are a senior engineer making a focused change to an existing project. Change only what "
    "the request needs and keep everything else as it is. Return each changed or new file in "
    "full as a `### <path>` line followed by one fenced code block. Do not return unchanged files. "
    "Only import modules that exist in the project or that you add."
)


@dataclass
class EditResult:
    status: str                       # applied | rolled_back | no_changes | rejected
    request: str
    changed_files: List[str] = field(default_factory=list)
    context_files: List[str] = field(default_factory=list)
    rejected_paths: Dict[str, str] = field(default_factory=dict)
    before: Dict[str, Any] = field(default_factory=dict)
    after: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _read_files(project: Path) -> Dict[str, str]:
    from backend.routes.export import _read_project_dir
    return _read_project_dir(project)


def relevant_files(project: Path, request: str, files: Dict[str, str], limit: int = 8) -> List[str]:
    """Files the request touches, from the repository retriever; entry points as a fallback."""
    paths: List[str] = []
    try:
        from backend.repository.impact_analyzer import global_impact_analyzer
        from backend.repository.indexer import global_repository_indexer
        from backend.repository.retriever import global_repository_context_retriever
        from backend.repository.task_analyzer import global_repository_task_analyzer
        index = global_repository_indexer.index_repository(str(project), force_reindex=True)
        task = global_repository_task_analyzer.analyze_task(request, "CODING")
        impact = global_impact_analyzer.analyze_impact(task, index)
        _, selected = global_repository_context_retriever.retrieve_context(index, task, impact)
        paths = [p.replace("\\", "/") for p in selected]
    except Exception as e:  # noqa: BLE001 - retrieval is best-effort; keyword fallback below
        _logger.warning("Repository retrieval failed for %s: %s", project, e)
    words = {w for w in re.findall(r"[a-z][a-z0-9_]{2,}", request.lower())}
    scored = sorted(((sum(w in (p + c[:4000]).lower() for w in words), p) for p, c in files.items()),
                    reverse=True)
    paths += [p for score, p in scored if score > 0]
    for entry in ("backend/main.py", "main.py", "backend/src/app.js", "app/page.js", "frontend/src/App.jsx"):
        if entry in files:
            paths.append(entry)
    return [p for p in dict.fromkeys(paths) if p in files][:limit]


def _project_decisions(project_id: str, request: str) -> str:
    try:
        from backend.memory.memory_manager import global_memory_manager
        results = global_memory_manager.search(project_id, request, top_k=5)
        lines = [f"- {getattr(r, 'key', '')}: {getattr(r, 'value', '')}" for r in results]
        return "\n".join(line for line in lines if line.strip("- :"))
    except Exception:  # noqa: BLE001 - no recorded decisions is a normal state
        return ""


def _validate_paths(project: Path, changes: Dict[str, str]) -> Dict[str, str]:
    """Rejected path -> reason."""
    from backend.exporter.zipper import export_exclusion_reason
    rejected = {}
    for path in changes:
        reason = export_exclusion_reason(path)
        if not reason and not (project / path).resolve().is_relative_to(project.resolve()):
            reason = "path outside the project"
        if reason:
            rejected[path] = reason
    return rejected


def _measure(project: Path) -> Dict[str, Any]:
    from backend.services.project_tester import global_project_tester
    from backend.validation.quality_gate import run_quality_gate
    gate = run_quality_gate(project)
    tests = global_project_tester.run_tests(str(project))
    return {"gate_errors": gate.get("error_count", 0), "gate_messages": [e["message"] for e in gate.get("errors", [])][:10],
            "tests_status": tests.get("overall_status"), "tests_passed": tests.get("passed", 0),
            "tests_total": tests.get("total", 0)}


def _worse(before: Dict[str, Any], after: Dict[str, Any]) -> Optional[str]:
    if after["gate_errors"] > before["gate_errors"]:
        return f"the edit added {after['gate_errors'] - before['gate_errors']} blocking quality-gate error(s)"
    if before["tests_status"] == "PASS" and after["tests_status"] != "PASS":
        return "tests passed before the edit and fail after it"
    if after["tests_passed"] < before["tests_passed"]:
        return f"passing tests dropped from {before['tests_passed']} to {after['tests_passed']}"
    return None


def edit_project(project_dir: Path, request: str, project_id: str = "",
                 generate: Optional[Callable[[str, str], str]] = None) -> EditResult:
    """Apply a follow-up request to a project on disk. `generate(system, prompt)` defaults to the coding model."""
    from backend.repository.patch_engine import global_patch_engine
    from backend.validation.code_extractor import extract_files_from_agent_output

    project = Path(project_dir).resolve()
    files = _read_files(project)
    context = relevant_files(project, request, files)
    result = EditResult(status="no_changes", request=request, context_files=context)

    shown, used = [], 0
    for path in context:
        block = f"### {path}\n```\n{files[path]}\n```"
        if used + len(block) > MAX_CONTEXT_CHARS:
            break
        shown.append(block)
        used += len(block)
    decisions = _project_decisions(project_id or project.name, request)
    prompt = (f"Change request: {request}\n\n"
              + (f"Project decisions to respect:\n{decisions}\n\n" if decisions else "")
              + "Project files (all paths): " + ", ".join(sorted(files)) + "\n\n"
              + "Relevant files:\n\n" + "\n\n".join(shown))

    if generate is None:
        from backend.services.llm import generate_text

        def generate(system, user):
            return generate_text(system, user, task="coding")
    reply = generate(SYSTEM_PROMPT, prompt)

    changes = {p.replace("\\", "/").lstrip("/"): c for p, c in extract_files_from_agent_output(reply).items()}
    changes = {p: c for p, c in changes.items() if files.get(p) != c}
    result.rejected_paths = _validate_paths(project, changes)
    changes = {p: c for p, c in changes.items() if p not in result.rejected_paths}
    if not changes:
        result.reason = "the model proposed no applicable changes"
        return result
    if len(changes) > MAX_CHANGED_FILES:
        result.status, result.reason = "rejected", f"{len(changes)} files changed; the limit for one edit is {MAX_CHANGED_FILES}"
        return result

    result.before = _measure(project)
    originals = {p: files.get(p) for p in changes}           # None = file is new
    applied, ok = global_patch_engine.apply_changes(str(project), changes, reason=f"edit: {request[:80]}")
    if not ok:
        result.status, result.reason = "rejected", "the patch could not be applied"
        return result
    result.changed_files = applied
    result.after = _measure(project)

    regression = _worse(result.before, result.after)
    if regression:
        global_patch_engine.apply_changes(str(project), originals, reason="roll back edit")
        result.status, result.reason = "rolled_back", regression
        return result

    result.status = "applied"
    try:
        from backend.quality.version_manager import global_version_manager
        global_version_manager.create_snapshot(project_id=project_id or project.name, files_map=_read_files(project),
                                               repair_reason=f"Edit: {request[:120]}")
    except Exception as e:  # noqa: BLE001 - history is a convenience, the edit stands
        _logger.warning("Version snapshot after edit failed: %s", e)
    return result
