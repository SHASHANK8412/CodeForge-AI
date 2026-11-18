"""
Repo-aware repair context: which files a model needs to see to fix a failure, within a size budget.

Sending only the file that failed hides the definitions it uses (a model, a schema, a helper in another module);
sending the whole project does not fit a local model's context. The context is chosen from evidence in the failure:

1. **primary** - project files in the traceback frames and in the lint errors (in that order);
2. **defines** - files that define the symbols the error names (``name 'X' is not defined``, ``cannot import name 'X'``,
   ``has no attribute 'x'``), from a symbol map built with ``ast``;
3. **imports** - project modules the primary files import;
4. **test** - the failing tests (the specification: shown, never to be changed).

Files are shown in full while the budget lasts; the rest are shown as a summary (signatures only), so the model still
knows what exists and where.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

DEFAULT_BUDGET = 12_000          # characters of file content in a repair prompt


@dataclass
class RepairContext:
    files: List[Tuple[str, str]] = field(default_factory=list)       # (path, reason) in priority order
    full: List[str] = field(default_factory=list)                    # shown in full
    summarized: List[str] = field(default_factory=list)              # shown as signatures only
    text: str = ""

    @property
    def paths(self) -> List[str]:
        return [p for p, _ in self.files]


def _is_test(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return name.startswith("test_") or name.endswith("_test.py") or ".test." in name or ".spec." in name \
        or path.startswith("tests/") or "/tests/" in path


def traceback_files(output: str, files: Dict[str, str]) -> List[str]:
    """Project files named by traceback frames (``File "...", line N``) and pytest locations (``path.py:12:``),
    in order of appearance, skipping installed packages."""
    found: List[str] = []
    for m in re.finditer(r'(?m)File "([^"]+)", line \d+|^([\w./\\-]+\.(?:py|js|jsx|ts|tsx)):\d+', output or ""):
        raw = (m.group(1) or m.group(2) or "").replace("\\", "/")
        if "site-packages" in raw or "/lib/python" in raw:
            continue
        for rel in files:
            if raw == rel or raw.endswith("/" + rel):
                found.append(rel)
                break
    return list(dict.fromkeys(found))


def error_symbols(output: str) -> Set[str]:
    """Names the error message is about."""
    pats = [r"name '(\w+)' is not defined", r"cannot import name '(\w+)'", r"has no attribute '(\w+)'",
            r"'(\w+)' object has no attribute", r"module '([\w.]+)' has no attribute", r"No module named '([\w.]+)'",
            r"(\w+)\(\) (?:got an unexpected|missing \d+ required)", r"F821 [Uu]ndefined name `?'?(\w+)"]
    out: Set[str] = set()
    for p in pats:
        out.update(re.findall(p, output or ""))
    return out


def symbol_map(files: Dict[str, str]) -> Dict[str, List[str]]:
    """name -> files that define it (top-level functions, classes, assignments and class methods), Python only."""
    defs: Dict[str, List[str]] = {}
    for path, src in files.items():
        if not path.endswith(".py"):
            continue
        try:
            tree = ast.parse(src)
        except (SyntaxError, ValueError):
            continue
        for node in tree.body:
            names: List[str] = []
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.append(node.name)
                if isinstance(node, ast.ClassDef):
                    names += [b.name for b in node.body if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef))]
            elif isinstance(node, ast.Assign):
                names += [t.id for t in node.targets if isinstance(t, ast.Name)]
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                names.append(node.target.id)
            for n in names:
                defs.setdefault(n, []).append(path)
    return defs


def _module_file(module: str, files: Dict[str, str]) -> Optional[str]:
    base = module.replace(".", "/")
    for cand in (f"{base}.py", f"{base}/__init__.py", f"backend/{base}.py", f"backend/{base}/__init__.py"):
        if cand in files:
            return cand
    return None


def imported_files(path: str, files: Dict[str, str]) -> List[str]:
    """Project files that `path` imports (absolute and relative imports), Python only."""
    if not path.endswith(".py"):
        return []
    try:
        tree = ast.parse(files[path])
    except (SyntaxError, ValueError):
        return []
    pkg = path.rsplit("/", 1)[0].replace("/", ".") if "/" in path else ""
    out: List[str] = []
    for node in ast.walk(tree):
        mods: List[str] = []
        if isinstance(node, ast.Import):
            mods = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                parts = pkg.split(".") if pkg else []
                parts = parts[: len(parts) - (node.level - 1)] if node.level > 1 else parts
                base = ".".join(p for p in parts + ([base] if base else []) if p)
            mods = [base] + [f"{base}.{a.name}" for a in node.names]
        for m in mods:
            f = _module_file(m, files) if m else None
            if f and f != path:
                out.append(f)
    return list(dict.fromkeys(out))


def summarize(path: str, src: str, max_lines: int = 40) -> str:
    """Signatures only: what the file defines, without bodies."""
    keep: List[str] = []
    if path.endswith(".py"):
        for line in src.splitlines():
            s = line.strip()
            if s.startswith(("def ", "async def ", "class ", "@")) or (line and not line[0].isspace()
                                                                    and re.match(r"[A-Za-z_]\w*\s*[:=]", line)):
                keep.append(line.rstrip())
    else:
        for line in src.splitlines():
            if re.match(r"\s*(export\s+)?(default\s+)?(async\s+)?(function|class|const|let|interface|type)\b", line):
                keep.append(line.rstrip())
    return "\n".join(keep[:max_lines]) + ("\n..." if len(keep) > max_lines else "")


def build_repair_context(files: Dict[str, str], output: str, errors: Optional[List[dict]] = None,
                         budget: int = DEFAULT_BUDGET, extra: Optional[List[str]] = None) -> RepairContext:
    """The files a repair needs, in priority order, rendered within `budget` characters."""
    ranked: List[Tuple[str, str]] = []

    def add(path: str, reason: str) -> None:
        if path in files and path not in {p for p, _ in ranked}:
            ranked.append((path, reason))

    tb = traceback_files(output, files)
    for p in tb:
        if not _is_test(p):
            add(p, "in the traceback")
    for e in errors or []:
        add(str(e.get("file") or ""), "named in the lint errors")
    for p in extra or []:
        add(p, "named by the failure")
    primary = [p for p, _ in ranked]
    defs = symbol_map(files)
    for name in sorted(error_symbols(output + "\n" + "\n".join(str(e.get("message", "")) for e in errors or []))):
        for p in defs.get(name, []):
            add(p, f"defines `{name}`")
    for p in primary:
        for imp in imported_files(p, files):
            add(imp, f"imported by {p}")
    for p in tb:
        if _is_test(p):
            add(p, "failing test (the specification: do not change it)")

    ctx = RepairContext(files=ranked)
    blocks, used = [], 0
    for path, reason in ranked:
        full = f"### {path}  ({reason})\n```\n{files[path]}\n```"
        if used + len(full) <= budget or not ctx.full:        # the first (most implicated) file is always in full
            blocks.append(full)
            used += len(full)
            ctx.full.append(path)
        else:
            summary = f"### {path}  ({reason}; summary: signatures only)\n```\n{summarize(path, files[path])}\n```"
            if used + len(summary) <= budget * 1.25:
                blocks.append(summary)
                used += len(summary)
                ctx.summarized.append(path)
    ctx.text = "\n\n".join(blocks)
    return ctx
