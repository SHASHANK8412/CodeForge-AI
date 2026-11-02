"""
Independent grader for generated projects.

The pipeline reports its own status, but a system grading itself is not
evidence. This grader takes the files a run produced and measures them from
scratch, inside the sandbox (``AIFORGE_SANDBOX=docker`` for isolation):

1. **syntax**   every ``.py`` file parses (``ast.parse`` on the host; parsing
                does not execute code).
2. **boot**     a FastAPI app can be located and imported, and
                ``GET /openapi.json`` returns 200 through ``TestClient``.
                *Build success* = syntax OK and boot OK.
3. **routes**   the app's real route table is compared with the task's
                ``expected_routes`` -> requirement coverage.
4. **tests**    the project's own pytest suite is run with ``--junitxml``;
                pass/fail counts come from the XML, not from parsing output.

All numbers come from executing the code, never from the LLM's description
of what it wrote.
"""

from __future__ import annotations

import ast
import json
import os
import re
import secrets
import shutil
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from backend.execution.docker_sandbox import python_in_sandbox, run_sandboxed, sandbox_backend

PROBE_FILENAME = "_aiforge_probe.py"
JUNIT_FILENAME = ".aiforge_junit.xml"
IGNORED_DIRS = {"node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build"}

# Runs *inside* the sandbox. Locates the FastAPI app, lists routes, hits /openapi.json.
PROBE_SOURCE = r'''
import importlib.util, json, os, sys, traceback
ROOT = os.path.abspath(os.path.dirname(__file__))
for p in (ROOT, os.path.join(ROOT, "backend"), os.path.join(ROOT, "app")):
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)
MARK = os.environ["AIFORGE_PROBE_MARK"]
candidates = json.loads(os.environ["AIFORGE_PROBE_CANDIDATES"])
result = {"app_found": False, "app_module": None, "boots": False, "error": None, "routes": [], "openapi_status": None}
errors = []
for rel in candidates:
    mod_name = rel[:-3].replace("/", ".")
    if mod_name.endswith(".__init__"):
        mod_name = mod_name[: -len(".__init__")]
    try:
        try:
            module = importlib.import_module(mod_name)
        except ImportError:
            spec = importlib.util.spec_from_file_location(mod_name.replace(".", "_"), os.path.join(ROOT, rel))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        from fastapi import FastAPI
        app = next((v for v in vars(module).values() if isinstance(v, FastAPI)), None)
        if app is None:
            errors.append(f"{rel}: imported but no FastAPI instance found")
            continue
        result["app_found"] = True
        result["app_module"] = rel
        for r in app.routes:
            methods = sorted(getattr(r, "methods", None) or (["WEBSOCKET"] if type(r).__name__.startswith("WebSocket") else []))
            for m in methods:
                if m not in ("HEAD", "OPTIONS"):
                    result["routes"].append([m, r.path])
        from fastapi.testclient import TestClient
        resp = TestClient(app).get("/openapi.json")
        result["openapi_status"] = resp.status_code
        result["boots"] = resp.status_code == 200
        if not result["boots"]:
            result["error"] = f"/openapi.json returned {resp.status_code}: {resp.text[:300]}"
        break
    except BaseException as exc:
        errors.append(f"{rel}: {type(exc).__name__}: {exc}\n" + traceback.format_exc(limit=3)[-800:])
if not result["boots"] and result["error"] is None and errors:
    result["error"] = "\n".join(errors)[-2000:]
print(MARK + json.dumps(result))
'''


@dataclass
class GradeResult:
    sandbox: str = "local"
    files_total: int = 0
    python_files: int = 0
    syntax_ok: bool = False
    syntax_errors: List[str] = field(default_factory=list)
    app_found: bool = False
    app_module: Optional[str] = None
    app_boots: bool = False
    boot_error: Optional[str] = None
    build_success: bool = False
    routes_found: List[List[str]] = field(default_factory=list)
    routes_expected: int = 0
    routes_matched: int = 0
    routes_missing: List[str] = field(default_factory=list)
    route_coverage: Optional[float] = None
    test_files: int = 0
    tests_collected: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    tests_errored: int = 0
    tests_skipped: int = 0
    test_pass_rate: Optional[float] = None
    pytest_exit_code: Optional[int] = None
    pytest_output_tail: str = ""
    grade_duration_ms: float = 0.0

    def to_dict(self) -> Dict:
        return asdict(self)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _iter_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]
        for fn in filenames:
            yield Path(dirpath) / fn


def normalize_route(method: str, path: str) -> Tuple[str, str]:
    path = re.sub(r"\{[^}]*\}", "{}", path.strip())
    if len(path) > 1:
        path = path.rstrip("/")
    return method.upper(), path or "/"


def route_coverage(found: List[List[str]], expected: List[Tuple[str, str]]) -> Tuple[int, List[str]]:
    have = {normalize_route(m, p) for m, p in found}
    missing = [f"{m} {p}" for m, p in expected if normalize_route(m, p) not in have]
    return len(expected) - len(missing), missing


def is_test_file(rel: str, content: str) -> bool:
    name = rel.rsplit("/", 1)[-1]
    return (name.startswith("test_") or name.endswith("_test.py")) and name.endswith(".py") and "def test" in content


def app_candidates(root: Path, py_files: List[Path]) -> List[str]:
    """Files that construct a FastAPI app, conventional entry points first."""
    preferred = ["backend/main.py", "main.py", "app/main.py", "backend/app/main.py", "src/main.py", "app.py",
                 "backend/app.py", "server.py"]
    hits = []
    for p in py_files:
        rel = p.relative_to(root).as_posix()
        if "test" in rel.rsplit("/", 1)[-1]:
            continue
        try:
            if re.search(r"\bFastAPI\s*\(", p.read_text(encoding="utf-8", errors="replace")):
                hits.append(rel)
        except OSError:
            continue
    ordered = [c for c in preferred if c in hits] + sorted(h for h in hits if h not in preferred)
    return ordered[:6]


def parse_junit(xml_path: Path) -> Dict[str, int]:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    for s in suites:
        for k in totals:
            totals[k] += int(s.attrib.get(k, 0) or 0)
    return totals


# --------------------------------------------------------------------------- #
# Grading
# --------------------------------------------------------------------------- #

def grade_project(project_dir: str, expected_routes: Optional[List[Tuple[str, str]]] = None,
                  timeout_seconds: float = 120.0) -> GradeResult:
    import time

    start = time.perf_counter()
    res = GradeResult(sandbox=sandbox_backend())
    src = Path(project_dir).resolve()
    if not src.is_dir():
        res.boot_error = f"project dir not found: {src}"
        return res

    scratch_root = Path(tempfile.mkdtemp(prefix="aiforge_grade_"))
    work = scratch_root / "work"
    try:
        shutil.copytree(src, work, ignore=shutil.ignore_patterns(*IGNORED_DIRS))
        files = list(_iter_files(work))
        res.files_total = len(files)
        py_files = [p for p in files if p.suffix == ".py"]
        res.python_files = len(py_files)

        # 1. syntax ---------------------------------------------------------
        test_files = []
        for p in py_files:
            rel = p.relative_to(work).as_posix()
            text = p.read_text(encoding="utf-8", errors="replace")
            try:
                ast.parse(text, filename=rel)
            except SyntaxError as exc:
                res.syntax_errors.append(f"{rel}:{exc.lineno}: {exc.msg}")
            if is_test_file(rel, text):
                test_files.append(rel)
        res.syntax_ok = res.python_files > 0 and not res.syntax_errors
        res.test_files = len(test_files)

        # 2./3. boot + routes ----------------------------------------------
        candidates = app_candidates(work, py_files)
        if candidates:
            mark = f"@@AIFORGE_PROBE_{secrets.token_hex(8)}@@"
            (work / PROBE_FILENAME).write_text(PROBE_SOURCE, encoding="utf-8")
            out = run_sandboxed(str(work), [python_in_sandbox(), PROBE_FILENAME],
                                timeout_seconds=min(60.0, timeout_seconds), keep_copy=str(work),
                                env={"AIFORGE_PROBE_MARK": mark,
                                     "AIFORGE_PROBE_CANDIDATES": json.dumps(candidates)})
            probe = _parse_probe(out.stdout, mark)
            if probe is None:
                res.boot_error = ("probe produced no result" + (" (timed out)" if out.timed_out else "")
                                  + f"\n{out.stderr[-1500:]}")
            else:
                res.app_found = bool(probe.get("app_found"))
                res.app_module = probe.get("app_module")
                res.app_boots = bool(probe.get("boots"))
                res.boot_error = probe.get("error")
                res.routes_found = probe.get("routes") or []
            (work / PROBE_FILENAME).unlink(missing_ok=True)
        else:
            res.boot_error = "no module constructs a FastAPI() app"
        res.build_success = res.syntax_ok and res.app_boots

        if expected_routes:
            res.routes_expected = len(expected_routes)
            res.routes_matched, res.routes_missing = route_coverage(res.routes_found, expected_routes)
            res.route_coverage = round(res.routes_matched / res.routes_expected, 4)

        # 4. tests ----------------------------------------------------------
        if test_files:
            junit = work / JUNIT_FILENAME
            cmd = [python_in_sandbox(), "-m", "pytest", "-q", "-p", "no:cacheprovider",
                   f"--junitxml={JUNIT_FILENAME}", *test_files]
            out = run_sandboxed(str(work), cmd, timeout_seconds=timeout_seconds, keep_copy=str(work))
            res.pytest_exit_code = out.exit_code
            res.pytest_output_tail = (out.stdout + "\n" + out.stderr)[-2000:]
            if junit.exists():
                try:
                    t = parse_junit(junit)
                    res.tests_collected = t["tests"]
                    res.tests_failed = t["failures"]
                    res.tests_errored = t["errors"]
                    res.tests_skipped = t["skipped"]
                    res.tests_passed = max(0, t["tests"] - t["failures"] - t["errors"] - t["skipped"])
                except ET.ParseError:
                    pass
            ran = res.tests_collected - res.tests_skipped
            if ran > 0:
                res.test_pass_rate = round(res.tests_passed / ran, 4)
            elif res.test_files:
                # Test files exist but nothing ran (collection error, exit 2/5): 0%.
                res.test_pass_rate = 0.0
    finally:
        shutil.rmtree(scratch_root, ignore_errors=True)

    res.grade_duration_ms = round((time.perf_counter() - start) * 1000, 1)
    return res


def _parse_probe(stdout: str, mark: str) -> Optional[Dict]:
    for line in reversed(stdout.splitlines()):
        if line.startswith(mark):
            try:
                return json.loads(line[len(mark):])
            except json.JSONDecodeError:
                return None
    return None


def materialize_files(files: Dict[str, str], dest: str) -> Path:
    """Writes a ``{relative_path: content}`` manifest to ``dest`` (traversal-safe)."""
    root = Path(dest).resolve()
    root.mkdir(parents=True, exist_ok=True)
    for rel, content in (files or {}).items():
        clean = str(rel).replace("\\", "/").lstrip("/")
        target = (root / clean).resolve()
        if not str(target).startswith(str(root) + os.sep):
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content if isinstance(content, str) else str(content), encoding="utf-8")
    return root
