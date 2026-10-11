"""
Codebase intelligence: a structural map of a project, built by parsing (ast for Python, patterns
for JavaScript/TypeScript), never by running the project's code.

The scan stays inside the project folder and is bounded: dependency/build/cache folders, secret
and local-data files are skipped, files above MAX_FILE_BYTES are listed but not read, and the walk
stops at MAX_FILES or after SCAN_SECONDS.
"""

import ast
import json
import re
import time
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Tuple

from backend.exporter.zipper import export_exclusion_reason

MAX_FILES = 4000
MAX_FILE_BYTES = 512 * 1024
SCAN_SECONDS = 30.0
SKIP_DIRS = {"build", "dist", ".next", "out", "coverage", ".turbo", ".cache", "htmlcov", ".tox", ".idea"}
SOURCE_EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
MANIFESTS = {"requirements.txt", "requirements-dev.txt", "pyproject.toml", "setup.py", "setup.cfg", "Pipfile",
             "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"}
CONFIG_NAMES = {"Dockerfile", "docker-compose.yml", "docker-compose.yaml", "tsconfig.json", "pytest.ini", "tox.ini",
                "ruff.toml", ".ruff.toml", ".eslintrc", ".eslintrc.json", ".eslintrc.js", "eslint.config.js",
                "vite.config.js", "vite.config.ts", "next.config.js", "next.config.mjs", ".flake8", "mypy.ini",
                "jest.config.js", "vitest.config.ts", "vitest.config.js", ".env.example"}

_JS_ROUTE = re.compile(r"\b(app|router|server)\.(get|post|put|patch|delete)\(\s*['\"`]([^'\"`]+)['\"`]")
_JS_COMPONENT = re.compile(r"(?:export\s+default\s+)?function\s+([A-Z][A-Za-z0-9]*)\s*\(|const\s+([A-Z][A-Za-z0-9]*)\s*=\s*\(")
_JS_IMPORT = re.compile(r"(?:import\s+[^'\"]*from\s+|require\(\s*|import\(\s*)['\"]([^'\"]+)['\"]")
_JS_API_CALL = re.compile(r"\b(?:fetch|axios\.(?:get|post|put|patch|delete)|api\.(?:get|post|put|patch|delete))\(\s*[`'\"]([^`'\"]+)")
_NEXT_HANDLER = re.compile(r"export\s+(?:async\s+)?function\s+(GET|POST|PUT|PATCH|DELETE)\b")


def iter_project_files(root: Path) -> Iterator[Tuple[str, Path, int]]:
    """(relative path, absolute path, size) for every file the analysis may look at."""
    root = Path(root).resolve()
    deadline = time.monotonic() + SCAN_SECONDS
    count = 0
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            entries = sorted(current.iterdir(), key=lambda p: p.name)
        except OSError:
            continue
        for entry in entries:
            if time.monotonic() > deadline or count >= MAX_FILES:
                return
            rel = entry.relative_to(root).as_posix()
            if entry.is_symlink():
                continue                      # never follow links out of the project
            if entry.is_dir():
                if entry.name in SKIP_DIRS or export_exclusion_reason(rel + "/x"):
                    continue
                stack.append(entry)
                continue
            if export_exclusion_reason(rel):
                continue
            try:
                size = entry.stat().st_size
            except OSError:
                continue
            count += 1
            yield rel, entry, size


def read_text(path: Path, size: int) -> Optional[str]:
    if size > MAX_FILE_BYTES:
        return None
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def _python_facts(rel: str, source: str, facts: Dict[str, Any]) -> None:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        facts["unparseable"].append(rel)
        return
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                if (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)
                        and dec.func.attr in ("get", "post", "put", "patch", "delete", "route", "api_route")
                        and dec.args and isinstance(dec.args[0], ast.Constant) and isinstance(dec.args[0].value, str)):
                    facts["routes"].append({"method": dec.func.attr.upper(), "path": dec.args[0].value,
                                            "handler": node.name, "file": rel, "line": node.lineno})
        elif isinstance(node, ast.ClassDef):
            bases = {b.id if isinstance(b, ast.Name) else b.attr if isinstance(b, ast.Attribute) else "" for b in node.bases}
            has_table = any(isinstance(s, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__tablename__"
                                                              for t in s.targets) for s in node.body)
            if has_table or bases & {"Model", "Document"}:
                facts["models"].append({"name": node.name, "kind": "orm", "file": rel, "line": node.lineno})
            elif bases & {"BaseModel", "SQLModel"}:
                facts["models"].append({"name": node.name, "kind": "schema", "file": rel, "line": node.lineno})
    facts["python_imports"][rel] = sorted(imports)
    if re.search(r"^\s*app\s*=\s*(FastAPI|Flask)\(", source, re.M) or "if __name__ == \"__main__\"" in source:
        facts["entry_points"].append(rel)


def _js_facts(rel: str, source: str, facts: Dict[str, Any]) -> None:
    for m in _JS_ROUTE.finditer(source):
        facts["routes"].append({"method": m.group(2).upper(), "path": m.group(3), "handler": None, "file": rel,
                                "line": source.count("\n", 0, m.start()) + 1})
    if re.search(r"(^|/)app/api/.+/route\.(js|ts|mjs)$", rel):
        path = "/" + rel.split("app/", 1)[1].rsplit("/route.", 1)[0]
        for m in _NEXT_HANDLER.finditer(source):
            facts["routes"].append({"method": m.group(1), "path": path, "handler": m.group(1), "file": rel,
                                    "line": source.count("\n", 0, m.start()) + 1})
    if rel.endswith((".jsx", ".tsx")):
        for m in _JS_COMPONENT.finditer(source):
            facts["components"].append({"name": m.group(1) or m.group(2), "file": rel})
    facts["js_imports"][rel] = sorted({m.group(1) for m in _JS_IMPORT.finditer(source)})
    for m in _JS_API_CALL.finditer(source):
        facts["api_calls"].append({"target": m.group(1)[:200], "file": rel})
    if re.search(r"\.listen\(|createRoot\(|ReactDOM\.render\(", source):
        facts["entry_points"].append(rel)


def build_project_map(project_dir: Any) -> Dict[str, Any]:
    root = Path(project_dir).resolve()
    started = time.monotonic()
    facts: Dict[str, Any] = {"routes": [], "models": [], "components": [], "api_calls": [], "entry_points": [],
                             "python_imports": {}, "js_imports": {}, "unparseable": []}
    files, tests, manifests, configs, too_large = [], [], {}, [], []
    languages: Dict[str, int] = {}

    for rel, path, size in iter_project_files(root):
        files.append(rel)
        ext = path.suffix.lower()
        if ext:
            languages[ext] = languages.get(ext, 0) + 1
        name = path.name
        if re.match(r"(test_.*\.py|.*_test\.py|.*\.(test|spec)\.(js|jsx|ts|tsx|mjs))$", name) or "/__tests__/" in f"/{rel}":
            tests.append(rel)
        if name in CONFIG_NAMES:
            configs.append(rel)
        if ext not in SOURCE_EXT and name not in MANIFESTS:
            continue
        source = read_text(path, size)
        if source is None:
            if size > MAX_FILE_BYTES:
                too_large.append(rel)
            continue
        if name in MANIFESTS:
            manifests[rel] = _manifest_summary(name, source)
            continue
        if ext == ".py":
            _python_facts(rel, source, facts)
        else:
            _js_facts(rel, source, facts)

    local_python = {f.split("/")[0].removesuffix(".py") for f in files if f.endswith(".py")}
    import_edges = sum(1 for imps in facts["python_imports"].values() for i in imps if i in local_python)
    stack = []
    if any(f.endswith(".py") for f in files):
        stack.append("Python")
    if any("fastapi" in imps for imps in facts["python_imports"].values()):
        stack.append("FastAPI")
    pkg_deps = {d for m in manifests.values() for d in m.get("dependencies", [])}
    stack += [label for dep, label in (("react", "React"), ("next", "Next.js"), ("express", "Express"),
                                       ("vite", "Vite"), ("mongoose", "MongoDB")) if dep in pkg_deps]
    return {
        "root_name": root.name,
        "file_count": len(files),
        "files": files[:2000],
        "truncated": len(files) >= MAX_FILES,
        "languages": dict(sorted(languages.items(), key=lambda kv: -kv[1])),
        "stack": stack,
        "entry_points": sorted(set(facts["entry_points"])),
        "routes": facts["routes"][:300],
        "models": facts["models"][:300],
        "components": facts["components"][:300],
        "api_calls": facts["api_calls"][:300],
        "tests": tests,
        "manifests": manifests,
        "configs": sorted(configs),
        "local_import_edges": import_edges,
        "python_imports": facts["python_imports"],
        "js_imports": facts["js_imports"],
        "unparseable": facts["unparseable"],
        "too_large": too_large,
        "scan_seconds": round(time.monotonic() - started, 2),
    }


def _manifest_summary(name: str, source: str) -> Dict[str, Any]:
    if name == "package.json":
        try:
            data = json.loads(source)
        except ValueError:
            return {"type": "npm", "error": "invalid JSON"}
        deps = sorted(set(data.get("dependencies", {})) | set(data.get("devDependencies", {})))
        return {"type": "npm", "dependencies": deps, "scripts": sorted(data.get("scripts", {}))}
    if name.startswith("requirements"):
        deps = [re.split(r"[<>=!~\[;\s]", line.strip())[0].lower()
                for line in source.splitlines() if line.strip() and not line.strip().startswith(("#", "-"))]
        return {"type": "pip", "dependencies": sorted(set(d for d in deps if d))}
    return {"type": name}
