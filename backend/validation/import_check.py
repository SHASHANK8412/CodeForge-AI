"""
Cross-file import check for generated Python projects.

Linters check one file at a time, so they miss the most common multi-file defect in generated
projects: imports of project modules that were never written (`from models.session import
Session` with no models/session.py), names that the imported module does not define, and a
module shadowed by a package of the same name (models.py next to models/). These are reported
as blocking errors so the debug loop gets a precise message instead of a collection failure.

The check is static (ast only); it never imports or runs the generated code.
"""

import ast
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

_EXCLUDE = {".venv", "venv", "node_modules", "dist", "build", "__pycache__", ".aiforge_checkpoints", ".git"}


def _py_files(project: Path) -> List[Path]:
    return [p for p in project.rglob("*.py") if not _EXCLUDE & set(p.relative_to(project).parts)]


def _issue(project: Path, path: Path, line: Optional[int], code: str, message: str) -> Dict[str, Any]:
    return {"tool": "imports", "severity": "error", "code": code,
            "file": path.relative_to(project).as_posix(), "line": line, "message": message}


def _resolve(roots: Iterable[Path], dotted: str) -> Optional[Path]:
    """The module file or package directory for a dotted name, searching each import root."""
    parts = dotted.split(".")
    for root in roots:
        base = root.joinpath(*parts)
        if base.is_dir() and any(base.glob("*.py")):
            return base
        if base.with_suffix(".py").is_file():
            return base.with_suffix(".py")
    return None


def _defined_names(module_file: Path) -> Optional[Set[str]]:
    """Top-level names a module defines, or None when it cannot be known (star import, __getattr__)."""
    try:
        tree = ast.parse(module_file.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return None  # reported by ruff
    names: Set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                names.update(n.id for n in ast.walk(t) if isinstance(n, ast.Name))
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if alias.name == "*":
                    return None
                names.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, (ast.If, ast.Try, ast.With)):
            return None  # conditional definitions: too dynamic to judge statically
    return None if "__getattr__" in names else names


def _roots_for(project: Path, path: Path) -> List[Path]:
    """Import roots a file may be run from: the project root, and its top-level app folder
    (generated projects are started either from the root or with `cd backend && uvicorn main:app`)."""
    parts = path.relative_to(project).parts
    return [project] + ([project / parts[0]] if len(parts) > 1 else [])


def local_import_issues(project_dir: Any) -> List[Dict[str, Any]]:
    project = Path(project_dir).resolve()
    files = _py_files(project)
    issues: List[Dict[str, Any]] = []

    # Module shadowed by a package of the same name.
    for f in files:
        pkg = f.with_suffix("")
        if f.name != "__init__.py" and pkg.is_dir() and any(pkg.glob("*.py")):
            issues.append(_issue(project, f, None, "AIF-shadowed-module",
                                 f"`{f.name}` is shadowed by the package `{pkg.name}/`: `import {pkg.name}` "
                                 f"loads {pkg.name}/__init__.py, so nothing in {f.name} is importable"))

    for f in files:
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        roots = _roots_for(project, f)
        # Only names backed by Python code count as local: a "redis/" config folder must not
        # turn `import redis` into a project import.
        local_tops = {p.stem if p.suffix == ".py" else p.name
                      for r in roots for p in r.iterdir()
                      if p.suffix == ".py" or (p.is_dir() and p.name not in _EXCLUDE and any(p.glob("*.py")))}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top in local_tops and _resolve(roots, alias.name) is None:
                        issues.append(_issue(project, f, node.lineno, "AIF-unresolved-import",
                                             f"Unresolved local import `{alias.name}`: no such module in the project"))
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    base = f.parent
                    for _ in range(node.level - 1):
                        base = base.parent
                    search, dotted = [base], node.module or ""
                else:
                    if not node.module or node.module.split(".")[0] not in local_tops:
                        continue  # stdlib or third-party: checked when the tests run
                    search, dotted = roots, node.module
                target = _resolve(search, dotted) if dotted else base
                shown = "." * node.level + (node.module or "")
                if target is None:
                    issues.append(_issue(project, f, node.lineno, "AIF-unresolved-import",
                                         f"Unresolved local import `{shown}`: no such module in the project"))
                    continue
                module_file = target / "__init__.py" if target.is_dir() else target
                defined = _defined_names(module_file) if module_file.is_file() else set()
                if defined is None:
                    continue
                for alias in node.names:
                    if alias.name == "*" or alias.name in defined:
                        continue
                    if target.is_dir() and _resolve([target], alias.name):
                        continue  # a submodule of the package
                    issues.append(_issue(project, f, node.lineno, "AIF-missing-name",
                                         f"`{alias.name}` is not defined in local module `{shown}` "
                                         f"({module_file.relative_to(project).as_posix()})"))
    return issues
