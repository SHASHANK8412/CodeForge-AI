"""
Repair strategies for the debug -> patch -> retest loop.

Deterministic fixes come first: they are exact, fast and safe. The LLM rewrite of a single file
is the fallback, and its output is only accepted if it parses and actually changes the file.
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


def llm_rewrite_file(files: Dict[str, str], output: str, errors: List[Dict[str, Any]]) -> Dict[str, str]:
    """Ask the coding model for a corrected version of the single most implicated file."""
    if os.environ.get("AIFORGE_LLM_REPAIR", "1").strip().lower() in ("0", "false", "no"):
        return {}
    rel = _implicated_file(files, output, errors)
    if not rel:
        return {}
    original = files[rel]
    error_text = "\n".join(f"{e.get('file')}:{e.get('line')}: {e.get('message')}" for e in (errors or [])[:20])
    prompt = (
        f"The file `{rel}` in a generated project fails. Errors:\n{error_text}\n\n"
        f"Test/runtime output (tail):\n{output[-3000:]}\n\n"
        f"Current contents of `{rel}`:\n```\n{original}\n```\n\n"
        "Return the complete corrected file in a single fenced code block and nothing else. "
        "Fix only what the errors require; keep everything else unchanged."
    )
    try:
        from backend.services.llm import generate_text
        reply = generate_text("You are a precise senior engineer fixing a bug in one file.", prompt, task="debugging")
    except Exception as e:  # noqa: BLE001 - model unavailable: no fix rather than a broken one
        _logger.warning("LLM repair unavailable for %s: %s", rel, e)
        return {}
    m = re.search(r"```[a-zA-Z0-9]*\n(.*?)```", reply, re.S)
    fixed = (m.group(1) if m else "").rstrip() + "\n"
    if not fixed.strip() or fixed.strip() == original.strip():
        return {}
    if rel.endswith(".py"):
        try:
            ast.parse(fixed)
        except SyntaxError:
            _logger.warning("LLM repair for %s did not parse; discarded", rel)
            return {}
        before, after = _blocking_issue_count(original), _blocking_issue_count(fixed)
        if after is not None and before is not None and after > before:
            _logger.warning("LLM repair for %s added blocking issues (%s -> %s); discarded", rel, before, after)
            return {}
    return {rel: fixed}


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


def propose_repairs(files: Dict[str, str], output: str, errors: List[Dict[str, Any]]) -> Tuple[str, Dict[str, str]]:
    """(strategy name, {file: new content}); empty changes when nothing applicable was found."""
    for name, strategy in (
        ("add_missing_imports", lambda: fix_undefined_names(files, errors, output)),
        ("add_missing_requirements", lambda: fix_missing_modules(files, output)),
        ("fix_literal_assertion", lambda: fix_literal_assertion(files, output)),
        ("llm_rewrite_file", lambda: llm_rewrite_file(files, output, errors)),
    ):
        changes = {k: v for k, v in strategy().items() if v != files.get(k)}
        if changes:
            return name, changes
    return "none", {}
