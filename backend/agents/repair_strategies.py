"""
Repair strategies for the debug -> patch -> retest loop.

Deterministic fixes come first: they are exact, fast and safe. The LLM rewrite of a single file
is the fallback, and its output is only accepted if it parses, changes the file and does not add
blocking lint errors.
No strategy comments code out or returns a file unchanged as a "fix".
"""

import ast
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

_logger = logging.getLogger("aiforge.agents.repair")

# Names LLM-generated FastAPI/SQLAlchemy code commonly uses without importing.
KNOWN_IMPORTS: Dict[str, str] = {
    **{n: f"from fastapi import {n}" for n in (
        "FastAPI", "APIRouter", "Depends", "HTTPException", "Request", "Response", "Query", "Path",
        "Body", "Header", "Form", "File", "UploadFile", "BackgroundTasks", "status")},
    "CORSMiddleware": "from fastapi.middleware.cors import CORSMiddleware",
    "JSONResponse": "from fastapi.responses import JSONResponse",
    "OAuth2PasswordBearer": "from fastapi.security import OAuth2PasswordBearer",
    "OAuth2PasswordRequestForm": "from fastapi.security import OAuth2PasswordRequestForm",
    "TestClient": "from fastapi.testclient import TestClient",
    **{n: f"from pydantic import {n}" for n in ("BaseModel", "Field", "EmailStr", "ValidationError", "ConfigDict")},
    **{n: f"from typing import {n}" for n in ("List", "Dict", "Optional", "Any", "Union", "Tuple", "Set", "Annotated")},
    **{n: f"from datetime import {n}" for n in ("datetime", "timedelta", "date", "timezone")},
    **{n: f"from sqlalchemy import {n}" for n in (
        "create_engine", "Column", "Integer", "String", "Boolean", "DateTime", "Float", "Text",
        "ForeignKey", "select", "func")},
    **{n: f"from sqlalchemy.orm import {n}" for n in ("Session", "sessionmaker", "relationship", "declarative_base")},
    "CryptContext": "from passlib.context import CryptContext",
    "JWTError": "from jose import JWTError",
    "jwt": "from jose import jwt",
    "load_dotenv": "from dotenv import load_dotenv",
    **{n: f"import {n}" for n in ("os", "sys", "json", "re", "time", "uuid", "logging", "secrets", "hashlib", "pytest")},
}

# Import name -> pip requirement, for modules that are missing from the environment.
PIP_NAMES: Dict[str, str] = {
    "fastapi": "fastapi", "pydantic": "pydantic", "sqlalchemy": "sqlalchemy", "uvicorn": "uvicorn",
    "jose": "python-jose[cryptography]", "jwt": "pyjwt", "passlib": "passlib[bcrypt]", "bcrypt": "bcrypt",
    "dotenv": "python-dotenv", "multipart": "python-multipart", "httpx": "httpx", "requests": "requests",
    "pytest": "pytest", "email_validator": "email-validator", "psycopg2": "psycopg2-binary",
    "aiosqlite": "aiosqlite", "starlette": "starlette", "redis": "redis", "pymongo": "pymongo",
}

_PYFILE = re.compile(r"\.py$")


def _insert_import(source: str, import_line: str) -> str:
    """Add an import after the module docstring / __future__ imports / existing imports."""
    lines = source.splitlines()
    insert_at = 0
    try:
        tree = ast.parse(source)
        for node in tree.body:
            is_doc = isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant) and isinstance(node.value.value, str)
            if is_doc or isinstance(node, (ast.Import, ast.ImportFrom)):
                insert_at = node.end_lineno or insert_at
            else:
                break
    except SyntaxError:
        pass
    lines.insert(insert_at, import_line)
    return "\n".join(lines) + ("\n" if source.endswith("\n") or not source else "")


def fix_undefined_names(files: Dict[str, str], errors: List[Dict[str, Any]], output: str = "") -> Dict[str, str]:
    """Add imports for undefined names reported by the quality gate (ruff F821) or NameErrors."""
    wanted: Dict[str, set] = {}
    for e in errors or []:
        m = re.search(r"Undefined name `([^`]+)`", e.get("message", ""))
        if m and e.get("file"):
            wanted.setdefault(e["file"], set()).add(m.group(1))
    for m in re.finditer(r'File "([^"]+\.py)", line \d+.*?\n(?:.*\n){0,6}?NameError: name \'(\w+)\' is not defined', output):
        path = m.group(1).replace("\\", "/")
        rel = next((k for k in files if path.endswith("/" + k) or path.endswith(k)), None)
        if rel:
            wanted.setdefault(rel, set()).add(m.group(2))

    changes: Dict[str, str] = {}
    for rel, names in wanted.items():
        source = changes.get(rel, files.get(rel))
        if source is None:
            continue
        for name in sorted(names):
            line = KNOWN_IMPORTS.get(name)
            if line and line not in source:
                source = _insert_import(source, line)
        if source != files.get(rel):
            changes[rel] = source
    return changes


def fix_missing_modules(files: Dict[str, str], output: str) -> Dict[str, str]:
    """Add missing third-party packages to requirements.txt."""
    missing = {m.group(1).split(".")[0] for m in re.finditer(r"No module named '([^']+)'", output)}
    local_packages = {k.split("/")[0] for k in files if "/" in k} | {k[:-3] for k in files if k.endswith(".py")}
    reqs_key = "requirements.txt" if "requirements.txt" in files or "backend/requirements.txt" not in files else "backend/requirements.txt"
    current = files.get(reqs_key, "")
    present = {re.split(r"[<>=\[ ]", l.strip())[0].lower() for l in current.splitlines() if l.strip()}
    additions = []
    for mod in sorted(missing - local_packages):
        pip_name = PIP_NAMES.get(mod)
        if pip_name and re.split(r"[\[]", pip_name)[0].lower() not in present:
            additions.append(pip_name)
    if not additions:
        return {}
    return {reqs_key: (current.rstrip("\n") + "\n" if current.strip() else "") + "\n".join(additions) + "\n"}


def fix_misplaced_imports(files: Dict[str, str], errors: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    A well-known library name imported from a project module that does not define it, e.g.
    `from backend.database import engine, Session` where Session is SQLAlchemy's: import it from
    the library instead (seen in a real run with qwen2.5-coder).
    """
    wanted: Dict[str, Dict[int, set]] = {}
    for e in errors or []:
        m = re.search(r"`([^`]+)` is not defined in local module", e.get("message", ""))
        if e.get("code") == "AIF-missing-name" and m and m.group(1) in KNOWN_IMPORTS and e.get("file") in files:
            wanted.setdefault(e["file"], {}).setdefault(int(e.get("line") or 0), set()).add(m.group(1))

    changes: Dict[str, str] = {}
    for rel, by_line in wanted.items():
        source = files[rel]
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        lines = source.split("\n")
        moved: List[str] = []
        for node in sorted((n for n in tree.body if isinstance(n, ast.ImportFrom) and n.lineno in by_line),
                           key=lambda n: n.lineno, reverse=True):
            names = by_line[node.lineno]
            keep = [a for a in node.names if a.name not in names]
            moved += [a.name for a in node.names if a.name in names]
            module = "." * node.level + (node.module or "")
            new_line = (f"from {module} import " + ", ".join(
                a.name + (f" as {a.asname}" if a.asname else "") for a in keep)) if keep else None
            start, end = node.lineno - 1, (node.end_lineno or node.lineno)
            lines[start:end] = [new_line] if new_line else []
        fixed = "\n".join(lines)
        for name in sorted(set(moved)):
            if KNOWN_IMPORTS[name] not in fixed:
                fixed = _insert_import(fixed, KNOWN_IMPORTS[name])
        if fixed != source:
            changes[rel] = fixed
    return changes


def fix_shadowed_module(files: Dict[str, str], errors: List[Dict[str, Any]]) -> Dict[str, Optional[str]]:
    """
    `x.py` next to a package `x/` is unreachable: `import x` loads the package. When the package's
    __init__.py is empty, move the module's code into it and delete the module. If both have code,
    merging needs judgement and is left to the LLM strategy.
    """
    changes: Dict[str, Optional[str]] = {}
    for e in errors or []:
        rel = e.get("file", "")
        if e.get("code") != "AIF-shadowed-module" or rel not in files or not rel.endswith(".py"):
            continue
        init = rel[:-3] + "/__init__.py"
        if files.get(init, "").strip():
            continue
        changes[init] = files[rel]
        changes[rel] = None
    return changes


def fix_literal_assertion(files: Dict[str, str], output: str) -> Dict[str, str]:
    """
    A test fails with `assert '<got>' == '<expected>'` and exactly one non-test source file contains
    the literal '<got>' once: replace it with '<expected>'. Narrow on purpose; anything ambiguous
    is left to the LLM strategy.
    """
    m = re.search(r"assert (['\"])(.+?)\1 == (['\"])(.+?)\3", output)
    if m:
        got, expected = m.group(2), m.group(4)
    else:
        m = re.search(r"expected (['\"])(.+?)\1,? got (['\"])(.+?)\3", output)
        if not m:
            return {}
        expected, got = m.group(2), m.group(4)
    candidates = []
    for rel, content in files.items():
        if not _PYFILE.search(rel) or "test" in rel.lower().split("/")[-1]:
            continue
        hits = [q for q in ("'", '"') if f"{q}{got}{q}" in content]
        if sum(content.count(f"{q}{got}{q}") for q in hits) == 1:
            candidates.append((rel, hits[0]))
    if len(candidates) != 1:
        return {}
    rel, q = candidates[0]
    return {rel: files[rel].replace(f"{q}{got}{q}", f"{q}{expected}{q}")}


_MISSING_NAME = re.compile(r"`([^`]+)` is not defined in local module `([^`]+)` \(([^)]+)\)")


def _top_level_node(tree: ast.Module, name: str):
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == name:
            return node
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return node
    return None


def _imports_needed(node, source_tree: ast.Module, target_tree: ast.Module) -> List[str]:
    """Import lines (from the source module) for the names a moved definition uses that the target lacks."""
    import builtins
    defined = {n.name for n in target_tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    defined |= {t.id for n in target_tree.body if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)}
    defined |= {(a.asname or a.name).split(".")[0] for n in target_tree.body if isinstance(n, (ast.Import, ast.ImportFrom))
                for a in n.names}
    used = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)} - defined - set(dir(builtins))
    out = []
    for imp in source_tree.body:
        if isinstance(imp, ast.ImportFrom) and imp.module and not imp.level:
            for a in imp.names:
                if (a.asname or a.name) in used:
                    out.append(f"from {imp.module} import {a.name}" + (f" as {a.asname}" if a.asname else ""))
        elif isinstance(imp, ast.Import):
            for a in imp.names:
                if (a.asname or a.name.split(".")[0]) in used:
                    out.append(f"import {a.name}" + (f" as {a.asname}" if a.asname else ""))
    return out


def _drop_from_import(source: str, module: str, name: str) -> Optional[str]:
    """`source` with `name` removed from its `from <module> import ...` statement (the statement removed when empty)."""
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == module and not node.level \
                and any(a.name == name for a in node.names):
            keep = [a for a in node.names if a.name != name]
            indent = lines[node.lineno - 1][: len(lines[node.lineno - 1]) - len(lines[node.lineno - 1].lstrip())]
            new = (f"{indent}from {module} import " + ", ".join(
                a.name + (f" as {a.asname}" if a.asname else "") for a in keep) + "\n") if keep else ""
            return "".join(lines[: node.lineno - 1]) + new + "".join(lines[node.end_lineno:])
    return None


def fix_missing_local_names(files: Dict[str, str], errors: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    A project module imports a name another project module does not define (the import check's AIF-missing-name; seen
    when agents generated in parallel disagree on an interface). Deterministic repairs, never touching tests:

    * the tests import the name from that module (they are the specification): if a non-test module defines it, the
      definition moves into the module the tests import it from;
    * otherwise, if the importing module defines the name itself, the import of it is dropped;
    * otherwise, if exactly one other non-test module defines it, the import points there (unless that would make the
      two modules import each other).
    Every changed file must parse and gain no blocking lint issue; anything else is left to the model repair.
    """
    issues = []
    for e in errors or []:
        m = _MISSING_NAME.search(str(e.get("message", "")))
        if m and e.get("file") in files:
            issues.append((e["file"], m.group(1), m.group(2), m.group(3).replace("\\", "/")))
    if not issues:
        return {}
    needed_by_tests = {(name, module) for f, name, module, _ in issues if _is_test_path(f)}
    changes: Dict[str, str] = {}

    def current(rel: str) -> str:
        return changes.get(rel, files.get(rel, ""))

    def defines(rel: str, name: str) -> bool:
        try:
            return _top_level_node(ast.parse(current(rel)), name) is not None
        except SyntaxError:
            return False

    def module_of(rel: str) -> str:
        return rel[:-3].replace("/", ".").removesuffix(".__init__")

    for importer, name, module, target in sorted(set(issues)):
        if _is_test_path(importer) or target not in files or defines(target, name):
            continue
        definers = [r for r in files if r.endswith(".py") and not _is_test_path(r) and r != target and defines(r, name)]
        proposal: Dict[str, str] = {}
        if (name, module) in needed_by_tests and len(definers) == 1:
            src_rel = definers[0]
            source = current(src_rel)
            node = _top_level_node(ast.parse(source), name)
            segment = ast.get_source_segment(source, node, padded=False)
            if node is not None and segment:
                lines = source.splitlines(keepends=True)
                start = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
                moved_from = "".join(lines[: start - 1]) + "".join(lines[node.end_lineno:])
                deco = "".join(lines[start - 1: node.lineno - 1])
                moved_to = current(target).rstrip() + "\n\n\n" + deco + segment + "\n"
                for line in _imports_needed(node, ast.parse(source), ast.parse(current(target))):
                    moved_to = _insert_import(moved_to, line)
                proposal = {target: moved_to, src_rel: moved_from}
        elif (name, module) not in needed_by_tests and defines(importer, name):
            fixed = _drop_from_import(current(importer), module, name)
            if fixed is not None:
                proposal = {importer: fixed}
        elif (name, module) not in needed_by_tests and len(definers) == 1 and definers[0] != importer:
            other = module_of(definers[0])
            if f"import {module_of(importer)}" not in current(definers[0]) and \
                    f"from {module_of(importer)} import" not in current(definers[0]):
                fixed = _drop_from_import(current(importer), module, name)
                if fixed is not None:
                    proposal = {importer: _insert_import(fixed, f"from {other} import {name}")}
        if proposal and all(_acceptable(rel, current(rel), text) for rel, text in proposal.items()):
            changes.update(proposal)
    return {rel: text for rel, text in changes.items() if text != files.get(rel)}


def _implicated_file(files: Dict[str, str], output: str, errors: List[Dict[str, Any]]) -> Optional[str]:
    """The project source file named first in the traceback or the quality-gate errors."""
    for e in errors or []:
        if e.get("file") in files and "test" not in e["file"].split("/")[-1]:
            return e["file"]
    for m in re.finditer(r'File "([^"]+)", line \d+', output):
        path = m.group(1).replace("\\", "/")
        for rel in files:
            if (path.endswith("/" + rel) or path.endswith(rel)) and "test" not in rel.split("/")[-1] \
                    and "site-packages" not in path:
                return rel
    return None


def _acceptable(rel: str, original: str, fixed: str) -> bool:
    """A model's version of one file is used only if it parses and adds no blocking lint issue."""
    if not fixed.strip() or fixed.strip() == (original or "").strip():
        return False
    if rel.endswith(".py"):
        try:
            ast.parse(fixed)
        except SyntaxError:
            _logger.warning("LLM repair for %s did not parse; discarded", rel)
            return False
        before, after = _blocking_issue_count(original or ""), _blocking_issue_count(fixed)
        if after is not None and before is not None and after > before:
            _logger.warning("LLM repair for %s added blocking issues (%s -> %s); discarded", rel, before, after)
            return False
    return True


def _is_test_path(rel: str) -> bool:
    name = rel.rsplit("/", 1)[-1]
    return name.startswith("test_") or name.endswith("_test.py") or rel.startswith("tests/")


def llm_repair(files: Dict[str, str], output: str, errors: List[Dict[str, Any]],
               memory_user: Optional[str] = None, history: str = "") -> Tuple[str, Dict[str, str]]:
    """
    Ask the coding model to repair the failure with search/replace edits (backend/repair/edits.py), showing it the
    files the failure involves (backend/repair/context.py) and this user's verified fixes for similar errors
    (backend/repair/fix_memory.py). Edits that do not apply get one retry with the reason; a reply that is a whole
    file for the implicated path is still accepted (strategy ``llm_rewrite_file``). Test files are never changed.
    Returns (strategy, {path: new content}); empty when there is no acceptable change.
    """
    if os.environ.get("AIFORGE_LLM_REPAIR", "1").strip().lower() in ("0", "false", "no"):
        return "none", {}
    rel = _implicated_file(files, output, errors)
    if not rel:
        return "none", {}
    from backend.repair.context import build_repair_context
    from backend.repair.edits import INSTRUCTIONS, apply_edits, feedback, parse_edits
    from backend.repair.fix_memory import global_fix_memory, hint_text
    error_text = "\n".join(f"{e.get('file')}:{e.get('line')}: {e.get('message')}" for e in (errors or [])[:20])
    # Interface mismatches between modules: the module a missing name must be added to is shown, and when the tests
    # import it from there, the model is told the tests fix the interface.
    missing = [(e.get("file"), m.group(1), m.group(2), m.group(3)) for e in errors or []
               for m in [_MISSING_NAME.search(str(e.get("message", "")))] if m]
    interface = "".join(
        f"- `{name}` is imported from `{module}` but `{path}` does not define it"
        + (" - the tests import it from there, so define it in that file.\n" if _is_test_path(f or "") else ".\n")
        for f, name, module, path in missing)
    ctx = build_repair_context(files, output, errors, extra=[rel] + sorted({p for *_, p in missing if p in files}))
    hints = global_fix_memory.lookup(memory_user, f"{output}\n{error_text}")
    global_fix_memory.mark_suggested([h["id"] for h in hints])
    prompt = (
        f"A generated project fails. Errors:\n{error_text or '(none from the linter)'}\n\n"
        + (f"Interface mismatches between project modules:\n{interface}\n" if interface else "")
        + f""
        f"Test/runtime output (tail):\n{output[-3000:]}\n\n"
        f"The file most implicated is `{rel}`. Files involved in the failure:\n\n{ctx.text}\n\n"
        + (hint_text(hints) + "\n\n" if hints else "")
        + ("Earlier repair attempts in this run (rolled-back ones made things worse or changed nothing; do not "
           f"repeat them):\n{history}\n\n" if history else "")
        + INSTRUCTIONS + "\nFix only what the errors require. Test files are the specification: never change them."
    )
    system = "You are a precise senior engineer fixing a bug in a project."
    try:
        from backend.services.llm import generate_text
        reply = generate_text(system, prompt, task="debugging")
        edits = [e for e in parse_edits(reply) if not _is_test_path(e.path)]
        if edits:
            result = apply_edits(files, edits)
            if result.errors:
                retry = generate_text(system, f"{prompt}\n\nYour previous reply:\n{reply}\n\n{feedback(result)}",
                                      task="debugging")
                again = [e for e in parse_edits(retry) if not _is_test_path(e.path)]
                if again:
                    result = apply_edits(files, again)
            changed = {p: c for p, c in result.changed.items() if _acceptable(p, files.get(p, ""), c)}
            if changed and len(changed) == len(result.changed):
                return "llm_search_replace", changed
            return "none", {}
    except Exception as e:  # noqa: BLE001 - model unavailable: no fix rather than a broken one
        _logger.warning("LLM repair unavailable for %s: %s", rel, e)
        return "none", {}
    # No edit blocks: the reply may still be the corrected file in one fenced block (the older format).
    m = re.search(r"```[a-zA-Z0-9]*\n(.*?)```", reply, re.S)
    fixed = (m.group(1) if m else "").rstrip() + "\n"
    return ("llm_rewrite_file", {rel: fixed}) if _acceptable(rel, files[rel], fixed) else ("none", {})


def llm_rewrite_file(files: Dict[str, str], output: str, errors: List[Dict[str, Any]]) -> Dict[str, str]:
    """The model's repair as {path: content} (kept for callers of the older name)."""
    return llm_repair(files, output, errors)[1]


def _blocking_issue_count(source: str) -> Optional[int]:
    """Undefined names / syntax errors in one Python source (ruff), or None if ruff is unavailable."""
    import json
    import subprocess
    import sys
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "candidate.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(source)
        try:
            proc = subprocess.run([sys.executable, "-m", "ruff", "check", path, "--select", "E9,F63,F7,F82",
                                   "--output-format", "json", "--no-cache"], capture_output=True, text=True, timeout=60)
            return len(json.loads(proc.stdout or "[]"))
        except (OSError, subprocess.SubprocessError, ValueError):
            return None


def propose_repairs(files: Dict[str, str], output: str, errors: List[Dict[str, Any]],
                    memory_user: Optional[str] = None, rejected: Optional[set] = None,
                    history: str = "") -> Tuple[str, Dict[str, Optional[str]]]:
    """(strategy name, {file: new content, or None to delete}); empty when nothing applicable was found.
    Deterministic strategies first; then the model (search/replace edits, see llm_repair). A patch whose hash is in
    `rejected` (rolled back earlier in this run) is skipped, so the next strategy gets its turn."""
    from backend.execution.repair_policy import patch_hash
    rejected = rejected or set()
    for name, strategy in (
        ("add_missing_imports", lambda: fix_undefined_names(files, errors, output)),
        ("merge_shadowed_module", lambda: fix_shadowed_module(files, errors)),
        ("fix_misplaced_imports", lambda: fix_misplaced_imports(files, errors)),
        ("fix_missing_local_names", lambda: fix_missing_local_names(files, errors)),
        ("add_missing_requirements", lambda: fix_missing_modules(files, output)),
        ("fix_literal_assertion", lambda: fix_literal_assertion(files, output)),
    ):
        changes = {k: v for k, v in strategy().items() if v != files.get(k)}
        if changes and patch_hash(changes) not in rejected:
            return name, changes
    name, changes = llm_repair(files, output, errors, memory_user, history)
    changes = {k: v for k, v in changes.items() if v != files.get(k)}
    return (name, changes) if changes and patch_hash(changes) not in rejected else ("none", {})
