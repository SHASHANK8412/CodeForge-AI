"""
Targeted repairs for classified failures, by the responsible agent, within that agent's scope.

  1. deterministic strategies first (the Debug Agent's exact fixes: missing imports, shadowed modules, misplaced
     imports, missing requirements). The strategy that edits test assertions is never used: tests are the
     specification here and are read-only to repairs.
  2. dependency_resolver: a controlled component - it only adds a missing package (from the import that failed)
     or removes an uninstallable version pin, in requirements.txt / package.json; nothing else.
  3. the routed agent's model repair (its own system prompt), limited to the files of that agent's scope and
     the files the failure names, with lines holding secrets hidden from the model.
Every change is validated (inside the workspace, inside the agent's scope, not a test, not an env/secret file)
before it is written; rejected paths are recorded, never silently dropped.
"""

import logging
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from backend.execution_guardian.models import Failure

_logger = logging.getLogger("aiforge.execution_guardian.repair")
PRIORITY = ("dependency_install_error", "syntax_error", "compilation_error", "configuration_error",
            "database_connection_error", "backend_startup_error", "frontend_build_error", "api_contract_mismatch",
            "runtime_exception", "unit_test_failure", "integration_test_failure")
SECRET_FILES = re.compile(r"(^|/)(\.env(\..*)?|.*\.pem|.*\.key|id_rsa.*|credentials.*|secrets?\..*)$", re.I)


def agent_prompt(agent: str) -> Optional[str]:
    """The existing agent's own system prompt (AgentFactory / agent classes); None for the generic repair prompt."""
    try:
        if agent == "frontend":
            from backend.agents.factory import AgentFactory
            return AgentFactory.create_agent("frontend").system_prompt
        if agent == "backend":
            from backend.agents.factory import AgentFactory
            return AgentFactory.create_agent("backend").system_prompt
        if agent == "database":
            from backend.agents.factory import AgentFactory
            return AgentFactory.create_agent("database").system_prompt
    except Exception as e:  # noqa: BLE001 - fall back to the generic repair prompt, and say so
        _logger.warning("could not load the %s agent's prompt: %s", agent, e)
    return None


def is_test(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return ("/tests/" in f"/{path}" or "/__tests__/" in f"/{path}" or name.startswith("test_")
            or name.endswith(("_test.py", ".test.js", ".test.jsx", ".test.ts", ".spec.js", ".spec.ts")))


def in_scope(agent: str, path: str, stack: Dict[str, Any], failure_files: List[str]) -> Tuple[bool, str]:
    p = path.replace("\\", "/")
    if p.startswith("/") or ".." in p.split("/") or re.match(r"^[A-Za-z]:", p):
        return False, "outside the workspace"
    if SECRET_FILES.search(p):
        return False, "environment / secret files are never changed"
    if is_test(p):
        return False, "tests are read-only to repairs"
    fe = stack.get("frontend")
    fe_prefix = "" if fe in (None, ".") else f"{fe}/"
    is_fe = (fe is not None and (p.startswith(fe_prefix) if fe_prefix else p.endswith((".js", ".jsx", ".ts", ".tsx", ".vue", ".css", ".html", ".json"))))
    if agent == "dependency_resolver":
        return (p.rsplit("/", 1)[-1] in ("requirements.txt", "package.json"),
                "the dependency resolver only edits requirements.txt / package.json")
    if agent == "frontend":
        return (is_fe and p.rsplit("/", 1)[-1] not in ("package-lock.json",), "the Frontend Agent only edits frontend files")
    if agent == "database":
        low = p.lower()
        return (p.endswith((".py", ".sql")) and any(k in low for k in ("model", "schema", "migration", "database", "db"))
                and not is_fe, "the Database Agent only edits models / schema / database files")
    if agent == "backend":
        return (p.endswith(".py") and not is_fe, "the Backend Agent only edits Python backend files")
    if agent == "debug":
        return (p in failure_files, "the Debug Agent only edits the files the failure names")
    return False, f"unknown agent {agent}"


def validate(changes: Dict[str, Optional[str]], agent: str, stack: Dict[str, Any], workspace: Path,
             failure_files: List[str]) -> Tuple[Dict[str, Optional[str]], List[Dict[str, str]]]:
    accepted, rejected = {}, []
    root = workspace.resolve()
    for path, content in changes.items():
        ok, why = in_scope(agent, path, stack, failure_files)
        target = (root / path).resolve()
        if ok and root not in target.parents:
            ok, why = False, "outside the workspace"
        if ok:
            accepted[path] = content
        else:
            rejected.append({"path": path, "reason": why})
    return accepted, rejected


def _deterministic(files: Dict[str, str], output: str, errors: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Optional[str]]]:
    from backend.agents.repair_strategies import (fix_misplaced_imports, fix_missing_modules, fix_shadowed_module,
                                                  fix_undefined_names)
    for name, fn in (("add_missing_imports", lambda: fix_undefined_names(files, errors, output)),
                     ("merge_shadowed_module", lambda: fix_shadowed_module(files, errors)),
                     ("fix_misplaced_imports", lambda: fix_misplaced_imports(files, errors)),
                     ("add_missing_requirements", lambda: fix_missing_modules(files, output))):
        changes = {k: v for k, v in fn().items() if v != files.get(k)}
        if changes:
            return name, changes
    return "", {}


def _unpin(files: Dict[str, str], output: str) -> Dict[str, Optional[str]]:
    """'No matching distribution found for pkg==9.9.9' -> keep pkg, drop the version that does not exist."""
    req = files.get("requirements.txt")
    m = re.search(r"No matching distribution found for ([A-Za-z0-9_.\-\[\]]+)\s*(==|>=|<=|~=)\s*[\w.*]+", output)
    if req is None or not m:
        return {}
    name = m.group(1)
    lines = req.splitlines()
    new = [re.sub(rf"^\s*{re.escape(name)}\s*(==|>=|<=|~=)\s*[\w.*]+\s*$", name, ln, flags=re.I) for ln in lines]
    return {"requirements.txt": "\n".join(new) + "\n"} if new != lines else {}


def propose(failures: List[Failure], agent: str, workspace: Path, stack: Dict[str, Any], project_id: str,
            generate: Optional[Callable[[str, str], str]], requirements: str = "") -> Tuple[str, Dict[str, Optional[str]], str]:
    """(strategy, changes, note) for one group of failures routed to `agent`."""
    from backend.routes.export import _read_project_dir
    files = _read_project_dir(workspace)
    output = "\n".join(f.log_excerpt or f.summary for f in failures)
    failure_files = sorted({x for f in failures for x in f.files})
    if agent == "dependency_resolver":
        from backend.agents.repair_strategies import fix_missing_modules
        changes = {k: v for k, v in fix_missing_modules(files, output).items() if v != files.get(k)}
        if changes:
            return "add_missing_requirements", changes, ""
        changes = _unpin(files, output)
        return ("unpin_unavailable_version", changes, "") if changes else ("", {}, "no controlled dependency fix applies")
    errors: List[Dict[str, Any]] = []
    try:
        from backend.validation.quality_gate import run_quality_gate
        errors = run_quality_gate(workspace).get("errors") or []
    except Exception as e:  # noqa: BLE001 - deterministic strategies then run without lint errors
        _logger.info("quality gate unavailable for repair context: %s", e)
    strategy, changes = _deterministic(files, output, errors)
    if changes:
        return strategy, changes, ""
    if agent not in ("frontend", "backend", "database", "debug"):
        return "", {}, f"no repair strategy for {agent}"
    from backend.evolution.autopilot.executor import HiddenLineChanged, model_changes
    allowed = [f for f in failure_files if f in files and in_scope(agent, f, stack, failure_files)[0]]
    if not allowed:
        allowed = sorted(f for f in files if in_scope(agent, f, stack, failure_files)[0])[:5]
    if not allowed:
        return "", {}, f"no file in the {agent} agent's scope to repair"
    tests = [f for f in failure_files if is_test(f) and f in files]
    request = ("Repair the verification failure(s) below by changing the implementation (tests are the "
               "specification and must not change).\n" + "\n".join(
                   f"- [{f.category}] {f.summary}\n  next action: {f.next_action}\n  failing tests: {', '.join(f.failing_tests) or '-'}\n"
                   f"  log excerpt:\n{(f.log_excerpt or '')[-1200:]}" for f in failures)
               + (f"\n\nProject requirements:\n{requirements[:1500]}" if requirements else ""))
    try:
        changes = model_changes(workspace, project_id, allowed, tests, request, generate, topic=failures[0].summary,
                                system_prompt=agent_prompt(agent))
    except HiddenLineChanged as e:
        return f"model:{agent}", {}, f"rejected: the model altered a hidden secret line ({e})"
    except PermissionError as e:
        return f"model:{agent}", {}, str(e)
    return f"model:{agent}", {k: v for k, v in changes.items() if v != files.get(k)}, ""


def pick_group(failures: List[Failure], exhausted: set) -> List[Failure]:
    """The most upstream repairable failure category (a dependency failure blocks everything after it), and every
    current failure of that category routed to the same agent."""
    cands = [f for f in failures if f.repairable and f.responsible_agent and f.signature not in exhausted]
    if not cands:
        return []
    rank = {c: i for i, c in enumerate(PRIORITY)}
    first = min(cands, key=lambda f: rank.get(f.category, len(PRIORITY)))
    return [f for f in cands if f.category == first.category and f.responsible_agent == first.responsible_agent]
