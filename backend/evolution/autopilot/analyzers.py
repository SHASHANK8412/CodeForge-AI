"""
Issue discovery. Each analyzer reads the project (or runs a static tool on it) and returns raw
findings plus a record of what it ran. Nothing here executes the project's code; the test
analyzer only runs tests through the sandboxed check in validation.py, in a disposable copy.

Raw findings are dicts; findings.py turns them into Finding records with stable ids.
"""

import ast
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from backend.evolution.autopilot.codebase import iter_project_files, read_text
from backend.evolution.autopilot.models import ToolRun
from backend.evolution.autopilot.redact import redact

Raw = Dict[str, Any]
Result = Tuple[List[Raw], List[ToolRun]]
_EXCLUDE = [".venv", "venv", "node_modules", "dist", "build", "__pycache__", ".aiforge_checkpoints"]
LONG_FUNCTION_LINES = 80
NODE_BUILTINS = {"fs", "path", "os", "http", "https", "url", "crypto", "util", "events", "stream", "child_process",
                 "assert", "buffer", "net", "zlib", "querystring", "readline", "timers", "worker_threads", "test"}


def _raw(rule_id, analyzer, category, title, description, severity, confidence, file=None, line=None,
         end=None, evidence="", remediation="", validation="", fix_strategy="manual") -> Raw:
    return {"rule_id": rule_id, "analyzer": analyzer, "category": category, "title": title,
            "description": description, "severity": severity, "confidence": confidence, "file": file,
            "line_start": line, "line_end": end or line, "evidence": redact(evidence, 1500),
            "remediation": remediation, "validation": validation, "fix_strategy": fix_strategy}


class Sources:
    """Python and JS/TS sources of a project, read once and shared by the analyzers."""

    def __init__(self, project: Path):
        self.project = Path(project).resolve()
        self.python: Dict[str, str] = {}
        self.javascript: Dict[str, str] = {}
        self.text: Dict[str, str] = {}
        self.files: List[str] = []
        self.stopped: List[str] = []
        for rel, path, size in iter_project_files(self.project, self.stopped):
            self.files.append(rel)
            if path.suffix.lower() in (".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".json", ".env",
                                       ".yml", ".yaml", ".toml", ".cfg", ".ini", ".txt") or path.name.startswith(".env"):
                source = read_text(path, size)
                if source is None:
                    continue
                self.text[rel] = source
                if rel.endswith(".py"):
                    self.python[rel] = source
                elif path.suffix.lower() in (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"):
                    self.javascript[rel] = source
        self._trees: Dict[str, Optional[ast.AST]] = {}

    def tree(self, rel: str) -> Optional[ast.AST]:
        if rel not in self._trees:
            try:
                self._trees[rel] = ast.parse(self.python[rel])
            except SyntaxError:
                self._trees[rel] = None
        return self._trees[rel]

    def line(self, rel: Optional[str], line: Optional[int]) -> str:
        if not rel or not line or rel not in self.text:
            return ""
        lines = self.text[rel].splitlines()
        return lines[line - 1].strip() if 0 < line <= len(lines) else ""


# --- syntax ---------------------------------------------------------------------------------

def analyze_syntax(src: Sources) -> Result:
    found = []
    for rel in src.python:
        try:
            ast.parse(src.python[rel])
        except SyntaxError as e:
            found.append(_raw("PY-SYNTAX", "syntax", "syntax", f"Python syntax error in {rel}",
                              f"The file cannot be parsed: {e.msg}.", "critical", "confirmed", rel, e.lineno,
                              evidence=f"{rel}:{e.lineno}: {e.msg}\n{(e.text or '').rstrip()}",
                              remediation="Correct the statement so the module parses.",
                              validation="python_syntax check passes and the quality gate has no E999 error",
                              fix_strategy="model"))
    return found, [ToolRun(tool="python ast parser", status="ran", detail=f"{len(src.python)} Python files")]


# --- quality gate and lint ----------------------------------------------------------------------

def analyze_quality(src: Sources) -> Result:
    from backend.validation.quality_gate import run_quality_gate
    gate = run_quality_gate(src.project)
    runs = [ToolRun(tool="quality gate (ruff E9/F63/F7/F82, import check, oxlint)",
                    status="partial" if gate.get("skipped") else "ran",
                    detail=f"{gate.get('error_count', 0)} errors, {gate.get('warning_count', 0)} warnings"
                           + (f"; not checked: {', '.join(gate['skipped'])}" if gate.get("skipped") else ""))]
    syntax_files = {rel for rel in src.python if src.tree(rel) is None}
    found = []
    for issue in gate.get("errors", []) + gate.get("warnings", []):
        code, rel = str(issue.get("code") or ""), issue.get("file")
        if rel in syntax_files and (code.startswith("E9") or "syntax" in code):
            continue                                  # reported once, by the syntax analyzer
        is_error = issue.get("severity") == "error"
        strategy = "import_repair" if code.startswith("AIF-") or code == "F821" else "model"
        found.append(_raw(f"GATE-{code}", issue.get("tool", "quality_gate"), "quality",
                          f"{code}: {issue.get('message', '')[:120]}",
                          issue.get("message", ""), "high" if is_error else "low", "confirmed", rel, issue.get("line"),
                          evidence=f"{rel}:{issue.get('line') or '?'}: [{code}] {issue.get('message', '')}",
                          remediation=("Define or import the missing name/module, or correct the reference."
                                       if is_error else "Remove the unused code or use it."),
                          validation="the quality gate no longer reports this issue and error count does not rise",
                          fix_strategy=strategy if is_error else "manual"))

    unused, run = _ruff_unused(src.project)
    runs.append(run)
    found += unused
    return found, runs


def _ruff_unused(project: Path) -> Result:
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(project), "--select", "F401,F841", "--output-format", "json",
             "--no-cache", "--exclude", ",".join(_EXCLUDE)], capture_output=True, text=True, timeout=120)
        items = json.loads(proc.stdout or "[]")
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        return [], ToolRun(tool="ruff F401/F841", status="unavailable", detail=str(e)[:200])
    found = []
    for f in items:
        if f.get("code") not in ("F401", "F841"):
            continue                                  # syntax errors are the syntax analyzer's
        try:
            rel = Path(f["filename"]).resolve().relative_to(project).as_posix()
        except ValueError:
            continue
        line = (f.get("location") or {}).get("row")
        if rel.endswith("__init__.py"):
            # Usually a deliberate re-export: removing it can break `from package import name`.
            found.append(_raw(f"PY-{f.get('code')}", "ruff", "quality", f"{f.get('code')}: {f.get('message', '')[:120]}",
                              f.get("message", "") + " In a package __init__ this is often an intended re-export.",
                              "info", "likely", rel, line,
                              evidence=f"{rel}:{line}: [{f.get('code')}] {f.get('message', '')}",
                              remediation="List the name in __all__ if it is a re-export; otherwise remove it.",
                              validation="ruff no longer reports it; imports of the package still resolve"))
            continue
        found.append(_raw(f"PY-{f.get('code')}", "ruff", "quality", f"{f.get('code')}: {f.get('message', '')[:120]}",
                          f.get("message", ""), "low", "confirmed", rel, line,
                          evidence=f"{rel}:{line}: [{f.get('code')}] {f.get('message', '')}",
                          remediation="Remove the unused import or variable.",
                          validation="ruff no longer reports it; tests and quality gate do not regress",
                          fix_strategy="ruff_fix" if f.get("code") == "F401" else "model"))
    return found, ToolRun(tool="ruff F401/F841", status="ran", detail=f"{len(found)} unused imports/variables")


# --- tests ------------------------------------------------------------------------------------

_TEST_FILE = re.compile(r"(^|/)(test_[^/]*\.py|[^/]*_test\.py|[^/]*\.(test|spec)\.(js|jsx|ts|tsx|mjs))$")


def analyze_tests(src: Sources, run_tests: bool = False) -> Result:
    tests = [f for f in src.files if _TEST_FILE.search(f) or "/__tests__/" in f"/{f}"]
    code = [f for f in list(src.python) + list(src.javascript) if f not in tests]
    found, runs = [], []
    if code and not tests:
        found.append(_raw("TESTS-NONE", "tests", "tests", "The project has no automated tests",
                          f"{len(code)} source files and no test files (test_*.py, *_test.py, *.test.js, *.spec.ts).",
                          "medium", "confirmed", None, None,
                          evidence=f"source files: {len(code)}; test files: 0",
                          remediation="Add tests for the main API routes and business logic.",
                          validation="the test check runs and passes in the sandbox", fix_strategy="model"))
    runs.append(ToolRun(tool="test discovery", status="ran", detail=f"{len(tests)} test files"))
    if not run_tests or not tests:
        runs.append(ToolRun(tool="test execution", status="skipped",
                            detail="no tests to run" if not tests else "not requested for this analysis"))
        return found, runs
    from backend.evolution.autopilot.validation import check_tests
    result = check_tests(src.project)
    runs.append(ToolRun(tool="test execution", status="ran" if result.status in ("passed", "failed") else result.status,
                        detail=f"{result.status} in {result.environment}" +
                               (f"; {result.counts}" if result.counts else "")))
    if result.status == "failed":
        found.append(_raw("TESTS-FAILING", "tests", "tests", "The test suite fails",
                          "The project's tests ran in the sandbox and did not pass.", "high", "confirmed", None, None,
                          evidence=result.output[-1500:],
                          remediation="Fix the code under test (not the assertions) until the suite passes.",
                          validation="the test check passes in the sandbox; no other check regresses",
                          fix_strategy="model"))
    return found, runs


# --- dependencies ---------------------------------------------------------------------------------

def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.lower()).split("[")[0]


def analyze_dependencies(src: Sources) -> Result:
    from backend.agents.repair_strategies import PIP_NAMES
    found = []
    req_files = [f for f in src.text if Path(f).name in ("requirements.txt",)]
    declared = set()
    for f in req_files:
        for line in src.text[f].splitlines():
            line = line.strip()
            if line and not line.startswith(("#", "-")):
                declared.add(_norm(re.split(r"[<>=!~\[;\s]", line)[0]))
    pyproject = next((src.text[f] for f in src.text if Path(f).name == "pyproject.toml"), "")
    local = {f.split("/")[0].removesuffix(".py") for f in src.python} | {Path(f).stem for f in src.python}
    for rel in src.python:
        for part in Path(rel).parts[:-1]:
            local.add(part)
    stdlib = set(getattr(sys, "stdlib_module_names", ())) | {"__future__"}
    missing: Dict[str, Tuple[str, int]] = {}
    for rel in src.python:
        tree = src.tree(rel)
        if tree is None:
            continue
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                names = [node.module.split(".")[0]]
            for name in names:
                if name in stdlib or name in local or name in missing:
                    continue
                pip = PIP_NAMES.get(name, name)
                if _norm(pip) in declared or _norm(name) in declared or (pyproject and re.search(
                        rf"['\"]{re.escape(pip.split('[')[0])}", pyproject, re.I)):
                    continue
                missing[name] = (rel, node.lineno)
    for name, (rel, line) in sorted(missing.items()):
        pip = PIP_NAMES.get(name, name)
        found.append(_raw("DEP-PY-UNDECLARED", "dependencies", "dependencies",
                          f"Python package '{pip}' is imported but not declared",
                          f"`{name}` is imported in {rel} but no requirements file declares `{pip}`. "
                          "A fresh install will fail with ModuleNotFoundError.",
                          "medium", "likely", rel, line, evidence=f"{rel}:{line}: {src.line(rel, line)}",
                          remediation=f"Add `{pip}` to requirements.txt (or remove the import).",
                          validation="the requirement is declared; tests still pass", fix_strategy="add_requirements"
                          if PIP_NAMES.get(name) else "manual"))

    packages = {f: json.loads(src.text[f]) for f in src.text if Path(f).name == "package.json" and _is_json(src.text[f])}
    for rel, source in src.javascript.items():
        pkg = _nearest_package(rel, packages)
        if pkg is None:
            continue
        deps = set((packages[pkg].get("dependencies") or {})) | set((packages[pkg].get("devDependencies") or {})) \
            | set((packages[pkg].get("peerDependencies") or {}))
        seen = set()
        for m in re.finditer(r"(?:import\s+[^'\"]*?from\s+|import\s+|require\(\s*)['\"]([^'\"./][^'\"]*)['\"]", source):
            spec = m.group(1)
            if spec.startswith(("node:", "@/", "~/", "#", "virtual:")):
                continue
            name = "/".join(spec.split("/")[:2]) if spec.startswith("@") else spec.split("/")[0]
            if name in NODE_BUILTINS or name in deps or name in seen:
                continue
            seen.add(name)
            line = source.count("\n", 0, m.start()) + 1
            found.append(_raw("DEP-JS-UNDECLARED", "dependencies", "dependencies",
                              f"npm package '{name}' is imported but not declared",
                              f"`{name}` is imported in {rel} but {pkg} does not list it.", "medium", "likely", rel, line,
                              evidence=f"{rel}:{line}: {src.line(rel, line)}",
                              remediation=f"Add `{name}` to {pkg} (dependencies or devDependencies).",
                              validation="npm install and the build succeed in the sandbox"))
    return found, [ToolRun(tool="dependency declaration check", status="ran",
                           detail=f"{len(req_files)} requirements files, {len(packages)} package.json")]


def _is_json(text: str) -> bool:
    try:
        return isinstance(json.loads(text), dict)
    except ValueError:
        return False


def _nearest_package(rel: str, packages: Dict[str, Any]) -> Optional[str]:
    parts = rel.split("/")[:-1]
    while True:
        candidate = "/".join(parts + ["package.json"]) if parts else "package.json"
        if candidate in packages:
            return candidate
        if not parts:
            return None
        parts = parts[:-1]


# --- security -------------------------------------------------------------------------------------

def analyze_security(src: Sources) -> Result:
    from backend.deployment.secret_scanner import global_secret_scanner
    from backend.validation.quality_gate import _bandit_findings
    found, runs = [], []
    bandit = _bandit_findings(src.project)
    if bandit is None:
        runs.append(ToolRun(tool="bandit", status="unavailable", detail="Bandit could not run"))
    else:
        runs.append(ToolRun(tool="bandit", status="ran", detail=f"{len(bandit)} findings"))
        for b in bandit:
            sev = {"HIGH": "high", "MEDIUM": "medium"}.get(b.get("severity"), "low")
            conf = {"HIGH": "confirmed", "MEDIUM": "likely"}.get(b.get("confidence"), "suspected")
            found.append(_raw(f"SEC-BANDIT-{b.get('code')}", "bandit", "security", f"{b.get('code')}: {b.get('message', '')[:120]}",
                              b.get("message", ""), sev, conf, b.get("file"), b.get("line"),
                              evidence=f"{b.get('file')}:{b.get('line')}: {src.line(b.get('file'), b.get('line'))}",
                              remediation="Apply the secure alternative Bandit describes for this rule.",
                              validation="Bandit no longer reports it; tests and quality gate do not regress",
                              fix_strategy="model" if sev in ("high", "medium") else "manual"))
    scan = global_secret_scanner.scan_files({k: v for k, v in src.text.items()})
    runs.append(ToolRun(tool="secret scanner", status="ran", detail=f"{scan.total_findings} possible secrets"))
    for s in scan.findings:
        found.append(_raw("SEC-SECRET", "secret_scanner", "security", f"Possible committed secret: {s.secret_type}",
                          "A credential appears to be stored in the source. Anyone with the code can use it.",
                          "critical", "likely", s.file_path, s.line_number,
                          evidence=f"{s.file_path}:{s.line_number}: {s.secret_type} {s.masked_value}",
                          remediation="Remove the value, rotate the credential, and read it from an environment variable.",
                          validation="the secret scanner no longer reports it; the credential has been rotated",
                          fix_strategy="manual"))
    return found, runs


# --- maintainability ----------------------------------------------------------------------------------

def _functions(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node


def analyze_maintainability(src: Sources) -> Result:
    found = []
    bodies: Dict[str, List[Tuple[str, ast.AST]]] = {}
    for rel in src.python:
        tree = src.tree(rel)
        if tree is None:
            continue
        for fn in _functions(tree):
            length = (fn.end_lineno or fn.lineno) - fn.lineno + 1
            if length > LONG_FUNCTION_LINES:
                found.append(_raw("MAINT-LONG-FUNCTION", "maintainability", "maintainability",
                                  f"Long function {fn.name} ({length} lines)",
                                  f"`{fn.name}` is {length} lines long (limit {LONG_FUNCTION_LINES}), which makes it hard to test and change.",
                                  "low", "confirmed", rel, fn.lineno, fn.end_lineno,
                                  evidence=f"{rel}:{fn.lineno}-{fn.end_lineno}: def {fn.name}",
                                  remediation="Split it into smaller functions with one responsibility each.",
                                  validation="behaviour is unchanged: tests pass before and after", fix_strategy="model"))
            if len(fn.body) >= 4:
                key = hashlib.sha1(ast.dump(ast.Module(body=fn.body, type_ignores=[]), annotate_fields=False)
                                   .encode()).hexdigest()
                bodies.setdefault(key, []).append((rel, fn))
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                found.append(_raw("MAINT-BARE-EXCEPT", "maintainability", "maintainability", "Bare `except:` clause",
                                  "A bare except also catches KeyboardInterrupt and SystemExit and hides real errors.",
                                  "low", "confirmed", rel, node.lineno, evidence=f"{rel}:{node.lineno}: {src.line(rel, node.lineno)}",
                                  remediation="Catch the specific exceptions expected here (at least `Exception`).",
                                  validation="tests pass; quality gate unchanged", fix_strategy="model"))
    for group in bodies.values():
        if len(group) < 2:
            continue
        where = ", ".join(f"{rel}:{fn.lineno} {fn.name}" for rel, fn in group[:6])
        rel, fn = group[0]
        found.append(_raw("MAINT-DUPLICATE-FUNCTION", "maintainability", "maintainability",
                          f"Duplicated function body ({len(group)} copies)",
                          f"{len(group)} functions have an identical body: {where}.", "low", "confirmed", rel, fn.lineno,
                          fn.end_lineno, evidence=where,
                          remediation="Keep one implementation and call it from the other places.",
                          validation="tests pass before and after", fix_strategy="manual"))
    return found, [ToolRun(tool="maintainability rules (ast)", status="ran", detail=f"{len(src.python)} Python files")]


# --- performance (heuristic) ----------------------------------------------------------------------------

_QUERY_ATTRS = {"query", "execute", "filter", "find", "find_one", "get", "post", "scalars", "first", "all"}
_HTTP_OWNERS = {"requests", "httpx", "session", "db"}


def analyze_performance(src: Sources) -> Result:
    found = []
    for rel in src.python:
        tree = src.tree(rel)
        if tree is None:
            continue
        for fn in _functions(tree):
            if isinstance(fn, ast.AsyncFunctionDef):
                for node in ast.walk(fn):
                    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                            and node.func.attr == "sleep" and isinstance(node.func.value, ast.Name)
                            and node.func.value.id == "time"):
                        found.append(_raw("PERF-BLOCKING-SLEEP", "performance", "performance",
                                          f"time.sleep inside async function {fn.name}",
                                          "time.sleep blocks the event loop and stalls every other request.",
                                          "medium", "likely", rel, node.lineno,
                                          evidence=f"{rel}:{node.lineno}: {src.line(rel, node.lineno)}",
                                          remediation="Use `await asyncio.sleep(...)`.",
                                          validation="tests pass; the call is no longer blocking", fix_strategy="model"))
        for loop in ast.walk(tree):
            if not isinstance(loop, (ast.For, ast.AsyncFor, ast.While)):
                continue
            for node in ast.walk(ast.Module(body=loop.body, type_ignores=[])):
                if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                    continue
                owner = node.func.value
                owner_name = owner.id if isinstance(owner, ast.Name) else owner.attr if isinstance(owner, ast.Attribute) else ""
                if owner_name.lower() in _HTTP_OWNERS and node.func.attr in _QUERY_ATTRS:
                    found.append(_raw("PERF-CALL-IN-LOOP", "performance", "performance",
                                      f"{owner_name}.{node.func.attr}() inside a loop",
                                      "A database query or network call inside a loop runs once per item (N+1 pattern).",
                                      "low", "suspected", rel, node.lineno,
                                      evidence=f"{rel}:{node.lineno}: {src.line(rel, node.lineno)}",
                                      remediation="Fetch in one batched query/request outside the loop, if the data allows it.",
                                      validation="needs a measurement; tests must still pass", fix_strategy="manual"))
                    break
    return found, [ToolRun(tool="performance heuristics (ast)", status="ran",
                           detail="suspected patterns only; no profiling was performed")]


ANALYZERS: List[Tuple[str, Callable[..., Result]]] = [
    ("syntax", analyze_syntax),
    ("quality", analyze_quality),
    ("tests", analyze_tests),
    ("dependencies", analyze_dependencies),
    ("security", analyze_security),
    ("maintainability", analyze_maintainability),
    ("performance", analyze_performance),
]


def run_analyzers(project: Path, run_tests: bool = False) -> Tuple[List[Raw], List[ToolRun], Sources]:
    src = Sources(project)
    raws, runs = [], []
    if src.stopped:
        runs.append(ToolRun(tool="file scan", status="partial", detail="; ".join(src.stopped)))
    for name, analyzer in ANALYZERS:
        try:
            r, t = analyzer(src, run_tests=run_tests) if name == "tests" else analyzer(src)
        except Exception as e:                        # one broken analyzer does not stop the others
            r, t = [], [ToolRun(tool=name, status="error", detail=redact(f"{type(e).__name__}: {e}", 300))]
        raws += r
        runs += t
    return raws, runs, src
