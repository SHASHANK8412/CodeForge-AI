"""
Dependency graph extraction (Python via ast, JavaScript/TypeScript via patterns).

Nothing is executed. The walk is Autopilot's bounded project scan (no dependency/build/VCS
folders, no secret or local-data files, no symlinks, size and file-count limits), plus a time
budget for parsing. What the scan could not cover is listed in `limits`.

Edges are "established" when read directly from the code and "inferred" otherwise (see models.py).
"""

import ast
import hashlib
import posixpath
import re
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

from backend.evolution.autopilot.codebase import CONFIG_NAMES, MANIFESTS, iter_project_files, read_text
from backend.evolution.autopilot.redact import redact
from backend.twin.models import Edge, Node

PY_EXT = {".py"}
JS_EXT = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
JS_RESOLVE = (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")
DEFAULT_DEADLINE_SECONDS = 60.0
HTTP_METHODS = ("get", "post", "put", "patch", "delete")
NODE_BUILTINS = {"fs", "path", "os", "http", "https", "url", "crypto", "util", "events", "stream", "child_process",
                 "assert", "buffer", "net", "zlib", "querystring", "readline", "timers", "worker_threads"}
_TEST_NAME = re.compile(r"(^|/)(test_[^/]*\.py|[^/]*_test\.py|[^/]*\.(test|spec)\.(js|jsx|ts|tsx|mjs))$")
_JS_IMPORT = re.compile(
    r"""import\s+(?P<clause>[^'";]*?)\s+from\s+['"](?P<spec>[^'"]+)['"]"""
    r"""|import\s+['"](?P<bare>[^'"]+)['"]"""
    r"""|(?:const|let|var)\s+(?P<req_clause>[\w{}\s,:]+?)\s*=\s*require\(\s*['"](?P<req>[^'"]+)['"]\s*\)"""
    r"""|require\(\s*['"](?P<req2>[^'"]+)['"]\s*\)"""
    r"""|import\(\s*['"](?P<dyn>[^'"]+)['"]\s*\)""")
_JS_COMPONENT = re.compile(r"(?:export\s+(?:default\s+)?)?(?:function\s+([A-Z]\w*)\s*\(|(?:const|let)\s+([A-Z]\w*)\s*=\s*(?:\([^)]*\)|\w+)\s*=>)")
_JS_DEFAULT_EXPORT = re.compile(r"export\s+default\s+(?:function\s+)?([A-Z]\w*)")
_JS_ROUTE = re.compile(r"\b(app|router|server|\w+Router)\.(get|post|put|patch|delete)\(\s*['\"`]([^'\"`]+)['\"`]")
_NEXT_HANDLER = re.compile(r"export\s+(?:async\s+)?function\s+(GET|POST|PUT|PATCH|DELETE)\b")
_JS_API_CALL = re.compile(
    r"\b(?:fetch|axios(?:\.(get|post|put|patch|delete))?|(?:api|client|http|apiClient)\.(get|post|put|patch|delete))"
    r"\(\s*([`'\"])(.+?)\3")


def file_id(path: str) -> str:
    return f"file:{path}"


def _line_of(source: str, index: int) -> int:
    return source.count("\n", 0, index) + 1


def _ev(path: str, line: int, text: str) -> str:
    return redact(f"{path}:{line}: {text.strip()[:200]}")


def normalize_route(path: str) -> str:
    """'/api/items/{item_id}', '/api/items/:id', `${API}/api/items/${id}` -> '/api/items/*'."""
    path = re.sub(r"^https?://[^/]+", "", path.strip())
    path = re.sub(r"^\$\{[^}]*\}", "", path)                     # leading ${API_URL}
    path = path.split("?")[0].split("#")[0]
    segments = []
    for seg in path.strip("/").split("/"):
        if not seg:
            continue
        if seg.startswith((":", "{", "$", "[", "<")) or "${" in seg:
            seg = "*"
        segments.append(seg)
    return "/" + "/".join(segments)


def routes_match(route: str, call: str) -> bool:
    r, c = normalize_route(route).strip("/").split("/"), normalize_route(call).strip("/").split("/")
    if r == [""] or c == [""]:
        return False
    # a router may be mounted under a prefix the scan cannot see, so the route can be a suffix of the call
    if len(c) < len(r):
        return False
    tail = c[len(c) - len(r):]
    return all(a == b or a == "*" or b == "*" for a, b in zip(r, tail))


class GraphBuilder:
    def __init__(self, project: Path, deadline_seconds: float = DEFAULT_DEADLINE_SECONDS):
        self.project = Path(project).resolve()
        self.deadline = time.monotonic() + deadline_seconds
        self.deadline_seconds = deadline_seconds
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[Tuple[str, str, str], Edge] = {}
        self.unresolved: List[Dict[str, object]] = []
        self.limits: List[str] = []
        self.sources: Dict[str, str] = {}
        self.files: List[Tuple[str, int, int]] = []          # (rel, size, mtime_ns)
        self.symbols: Dict[str, Dict[str, str]] = {}         # file -> {name: node id}
        self.names: Dict[str, Set[str]] = {}                 # python file -> every module-level name
        self.default_export: Dict[str, str] = {}             # js file -> component node id
        self.too_large: List[str] = []
        self.unparseable: List[str] = []
        self.dynamic_imports: List[str] = []

    # --- graph helpers ------------------------------------------------------------------------

    def node(self, node_id: str, type_: str, **kw) -> str:
        if node_id not in self.nodes:
            self.nodes[node_id] = Node(id=node_id, type=type_, **kw)
        return node_id

    def edge(self, source: str, target: str, type_: str, evidence: str, certainty: str = "established") -> None:
        if source == target:
            return
        key = (source, target, type_)
        current = self.edges.get(key)
        if current is None or (current.certainty == "inferred" and certainty == "established"):
            self.edges[key] = Edge(source=source, target=target, type=type_, certainty=certainty, evidence=evidence)

    def out_of_time(self) -> bool:
        return time.monotonic() > self.deadline

    # --- scan -------------------------------------------------------------------------------------

    def scan(self) -> None:
        count = 0
        for rel, path, size in iter_project_files(self.project):
            count += 1
            try:
                mtime = path.stat().st_mtime_ns
            except OSError:
                mtime = 0
            self.files.append((rel, size, mtime))
            ext = path.suffix.lower()
            is_test = bool(_TEST_NAME.search(rel)) or "/__tests__/" in f"/{rel}"
            language = "python" if ext in PY_EXT else "javascript" if ext in JS_EXT else None
            if ext in PY_EXT or ext in JS_EXT:
                self.node(file_id(rel), "test" if is_test else "file", path=rel, language=language,
                          meta={"config": bool(re.search(r"(^|/)(config|settings)\.(py|js|ts)$", rel))})
                source = read_text(path, size)
                if source is None:
                    self.too_large.append(rel)
                    continue
                self.sources[rel] = source
                if re.search(r"^\s*\w+\s*=\s*(FastAPI|Flask)\(|__name__\s*==\s*['\"]__main__['\"]|\.listen\(|createRoot\(",
                             source, re.M):
                    self.nodes[file_id(rel)].meta["entry"] = True
            elif path.name in CONFIG_NAMES or path.name in MANIFESTS or path.name.startswith(".env.example"):
                self.node(file_id(rel), "config", path=rel, meta={"kind": path.name})
        from backend.evolution.autopilot.codebase import MAX_FILES
        if count >= MAX_FILES:
            self.limits.append(f"the project has more than {MAX_FILES} files; the rest were not analyzed")

    # --- python -----------------------------------------------------------------------------------

    def _python_roots(self) -> List[str]:
        tops = {rel.split("/")[0] for rel in self.sources if rel.endswith(".py") and "/" in rel}
        return [""] + sorted(t for t in tops if not (self.project / t / "__init__.py").exists())

    def _module_maps(self) -> Dict[str, Dict[str, str]]:
        maps: Dict[str, Dict[str, str]] = {}
        for root in self._python_roots():
            prefix = f"{root}/" if root else ""
            m: Dict[str, str] = {}
            for rel in self.sources:
                if not rel.endswith(".py") or not rel.startswith(prefix):
                    continue
                inner = rel[len(prefix):][:-3]
                if inner.endswith("/__init__"):
                    inner = inner[: -len("/__init__")]
                m[inner.replace("/", ".")] = rel
            maps[root] = m
        return maps

    def _resolve_py(self, importer: str, module: str, maps) -> Tuple[Optional[str], str]:
        """(file, certainty) for an absolute module name, trying the importer's own source root first."""
        top = importer.split("/")[0] if "/" in importer else ""
        order = ([top] if top in maps and top else []) + [""] + [r for r in maps if r not in ("", top)]
        for root in order:
            if module in maps.get(root, {}):
                # resolving through a sub-folder root assumes the code runs from that folder
                return maps[root][module], "established" if (root == "" or root == top) else "inferred"
        return None, ""

    def python(self) -> None:
        maps = self._module_maps()
        local_tops = {m.split(".")[0] for mp in maps.values() for m in mp}
        stdlib = set(getattr(sys, "stdlib_module_names", ())) | {"__future__"}
        trees: Dict[str, ast.AST] = {}
        for rel, source in self.sources.items():
            if not rel.endswith(".py"):
                continue
            try:
                trees[rel] = ast.parse(source)
            except SyntaxError as e:
                self.unparseable.append(rel)
                self.unresolved.append({"file": rel, "line": e.lineno, "module": None,
                                        "reason": f"file does not parse ({e.msg}); its dependencies are unknown"})
        for rel, tree in trees.items():
            self._python_definitions(rel, tree)
        for rel, tree in trees.items():
            if self.out_of_time():
                return
            self._python_imports(rel, tree, maps, local_tops, stdlib)

    def _python_definitions(self, rel: str, tree: ast.AST) -> None:
        fid = file_id(rel)
        table = self.symbols.setdefault(rel, {})
        names = self.names.setdefault(rel, set())
        for node in tree.body:                        # every module-level name, for `from m import x` checks
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                for t in (node.targets if isinstance(node, ast.Assign) else [node.target]):
                    names.update(n.id for n in ast.walk(t) if isinstance(n, ast.Name))
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                names.update((a.asname or a.name).split(".")[0] for a in node.names)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.add(node.name)
            elif isinstance(node, (ast.If, ast.Try, ast.With)):
                names.update(n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store))
                names.update((a.asname or a.name).split(".")[0] for n in ast.walk(node)
                             if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names)
        prefixes: Dict[str, str] = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                call = node.value
                fname = call.func.attr if isinstance(call.func, ast.Attribute) else getattr(call.func, "id", "")
                if fname == "APIRouter":
                    prefix = next((k.value.value for k in call.keywords if k.arg == "prefix"
                                   and isinstance(k.value, ast.Constant) and isinstance(k.value.value, str)), "")
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            prefixes[t.id] = prefix
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                type_ = "class"
                meta = {"line": node.lineno, "end_line": node.end_lineno}
                if isinstance(node, ast.ClassDef):
                    bases = {b.id if isinstance(b, ast.Name) else b.attr if isinstance(b, ast.Attribute) else ""
                             for b in node.bases}
                    has_table = any(isinstance(s, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__tablename__"
                                                                      for t in s.targets) for s in node.body)
                    if has_table or bases & {"Model", "Document"}:
                        type_, meta["kind"] = "model", "orm"
                    elif bases & {"BaseModel", "SQLModel"}:
                        type_, meta["kind"] = "model", "schema"
                else:
                    type_ = "function"
                sid = self.node(f"{type_}:{rel}#{node.name}", type_, path=rel, symbol=node.name, language="python", meta=meta)
                table[node.name] = sid
                self.edge(fid, sid, "defines", _ev(rel, node.lineno, f"{'class' if type_ != 'function' else 'def'} {node.name}"))
                if not isinstance(node, ast.ClassDef):
                    for dec in node.decorator_list:
                        if (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)
                                and dec.func.attr in HTTP_METHODS + ("api_route",)
                                and dec.args and isinstance(dec.args[0], ast.Constant) and isinstance(dec.args[0].value, str)):
                            owner = dec.func.value.id if isinstance(dec.func.value, ast.Name) else ""
                            path = prefixes.get(owner, "") + dec.args[0].value
                            method = dec.func.attr.upper() if dec.func.attr != "api_route" else "ANY"
                            rid = self.node(f"route:{rel}#{method} {path}", "route", path=rel, symbol=f"{method} {path}",
                                            language="python", meta={"method": method, "route": path, "line": dec.lineno,
                                                                     "handler": node.name})
                            self.edge(fid, rid, "defines", _ev(rel, dec.lineno, f"@{owner}.{dec.func.attr}({path!r})"))
                            self.edge(rid, sid, "handled_by", _ev(rel, node.lineno, f"def {node.name}"))

    def _python_imports(self, rel: str, tree: ast.AST, maps, local_tops: Set[str], stdlib: Set[str]) -> None:
        fid = file_id(rel)
        is_test = self.nodes[fid].type == "test"
        lines = self.sources[rel].splitlines()
        aliases: Dict[str, str] = {}                          # local name -> module file (for mod.Name usage)

        def text(lineno: int) -> str:
            return lines[lineno - 1] if 0 < lineno <= len(lines) else ""

        def link(target_file: str, lineno: int, certainty: str) -> None:
            self.edge(fid, file_id(target_file), "tests" if is_test else "imports",
                      _ev(rel, lineno, text(lineno)), certainty)

        def external_or_unresolved(name: str, lineno: int) -> None:
            top = name.split(".")[0]
            if top in stdlib:
                return
            if top in local_tops:
                self.unresolved.append({"file": rel, "line": lineno, "module": name,
                                        "reason": f"`{name}` looks like a project module but no file matches it"})
                return
            pid = self.node(f"package:{top}", "package", symbol=top, language="python")
            self.edge(fid, pid, "depends_on", _ev(rel, lineno, text(lineno)))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target, cert = self._resolve_py(rel, alias.name, maps)
                    if target:
                        link(target, node.lineno, cert)
                        aliases[alias.asname or alias.name.split(".")[0]] = target if alias.asname else ""
                    else:
                        external_or_unresolved(alias.name, node.lineno)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    parts = [p for p in posixpath.dirname(rel).split("/") if p]
                    up = node.level - 1
                    if up > len(parts):
                        self.unresolved.append({"file": rel, "line": node.lineno, "module": "." * node.level + (node.module or ""),
                                                "reason": "relative import goes above the project folder"})
                        continue
                    package = "/".join(parts[: len(parts) - up])
                    resolved_module = None
                    if node.module:
                        cand = posixpath.join(package, *node.module.split("."))
                        resolved_module = next((p for p in (cand + ".py", cand + "/__init__.py") if p in self.sources), None)
                    elif package and f"{package}/__init__.py" in self.sources:
                        resolved_module = f"{package}/__init__.py"
                    for alias in node.names:
                        sub = posixpath.join(package, *(node.module.split(".") if node.module else []), alias.name)
                        sub_file = next((p for p in (sub + ".py", sub + "/__init__.py") if p in self.sources), None)
                        if sub_file:
                            link(sub_file, node.lineno, "established")
                            aliases[alias.asname or alias.name] = sub_file
                        elif resolved_module:
                            link(resolved_module, node.lineno, "established")
                            self._use_symbol(fid, resolved_module, alias.name, rel, node.lineno, text(node.lineno))
                        else:
                            self.unresolved.append({"file": rel, "line": node.lineno,
                                                    "module": "." * node.level + (node.module or "") + f" ({alias.name})",
                                                    "reason": "relative import does not match a project file"})
                    continue
                module = node.module or ""
                target, cert = self._resolve_py(rel, module, maps)
                for alias in node.names:
                    sub, sub_cert = self._resolve_py(rel, f"{module}.{alias.name}", maps)
                    if sub:
                        link(sub, node.lineno, sub_cert)
                        aliases[alias.asname or alias.name] = sub
                    elif target:
                        link(target, node.lineno, cert)
                        if not self._use_symbol(fid, target, alias.name, rel, node.lineno, text(node.lineno)) \
                                and alias.name != "*" and alias.name not in self.names.get(target, set()) \
                                and target not in self.unparseable:
                            if not target.endswith("__init__.py"):
                                self.unresolved.append({"file": rel, "line": node.lineno, "module": f"{module}.{alias.name}",
                                                        "reason": f"`{alias.name}` is not defined at the top level of {target}"})
                    else:
                        external_or_unresolved(module, node.lineno)
                        break
            elif isinstance(node, ast.Call) and (
                    (isinstance(node.func, ast.Attribute) and node.func.attr == "import_module")
                    or (isinstance(node.func, ast.Name) and node.func.id == "__import__")):
                self.dynamic_imports.append(f"{rel}:{node.lineno}")
        # module.attribute usage of imported project modules: `import models` ... `models.Item`
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and aliases.get(node.value.id):
                self._use_symbol(fid, aliases[node.value.id], node.attr, rel, node.lineno, text(node.lineno))

    def _use_symbol(self, fid: str, target_file: str, name: str, rel: str, lineno: int, text: str) -> bool:
        sid = self.symbols.get(target_file, {}).get(name)
        if sid:
            self.edge(fid, sid, "uses", _ev(rel, lineno, text))
            return True
        return False

    # --- javascript / typescript ----------------------------------------------------------------------

    def _resolve_js(self, importer: str, spec: str) -> Tuple[Optional[str], str]:
        if spec.startswith("."):
            base = posixpath.normpath(posixpath.join(posixpath.dirname(importer), spec))
            certainty = "established"
            candidates = [base]
        elif spec.startswith(("@/", "~/")):
            # a bundler alias for the source folder: the usual setups are tried, so the match is inferred
            rest = spec[2:]
            parts = importer.split("/")
            src_dirs = ["src"] + ["/".join(parts[: i + 1]) for i, p in enumerate(parts[:-1]) if p == "src"]
            candidates = [posixpath.join(d, rest) for d in dict.fromkeys(src_dirs)]
            certainty = "inferred"
        else:
            return None, "package"
        for base in candidates:
            if base.startswith(".."):
                return None, "outside"
            for path in [base] + [base + e for e in JS_RESOLVE] + [f"{base}/index{e}" for e in JS_RESOLVE]:
                if path in self.sources or (path in {f for f, _, _ in self.files} and file_id(path) in self.nodes):
                    return path, certainty
        return None, "missing"

    def javascript(self) -> None:
        js = [rel for rel in self.sources if Path(rel).suffix.lower() in JS_EXT]
        for rel in js:
            self._js_definitions(rel, self.sources[rel])
        for rel in js:
            if self.out_of_time():
                return
            self._js_imports(rel, self.sources[rel])

    def _js_definitions(self, rel: str, source: str) -> None:
        fid = file_id(rel)
        table = self.symbols.setdefault(rel, {})
        if rel.endswith((".jsx", ".tsx")) or re.search(r"return\s*\(?\s*<[A-Za-z>]", source):
            for m in _JS_COMPONENT.finditer(source):
                name = m.group(1) or m.group(2)
                line = _line_of(source, m.start())
                cid = self.node(f"component:{rel}#{name}", "component", path=rel, symbol=name, language="javascript",
                                meta={"line": line})
                table[name] = cid
                self.edge(fid, cid, "defines", _ev(rel, line, m.group(0)))
            d = _JS_DEFAULT_EXPORT.search(source)
            if d and d.group(1) in table:
                self.default_export[rel] = table[d.group(1)]
        for m in _JS_ROUTE.finditer(source):
            method, path = m.group(2).upper(), m.group(3)
            line = _line_of(source, m.start())
            rid = self.node(f"route:{rel}#{method} {path}", "route", path=rel, symbol=f"{method} {path}",
                            language="javascript", meta={"method": method, "route": path, "line": line})
            self.edge(fid, rid, "defines", _ev(rel, line, m.group(0)))
        nm = re.search(r"(^|/)app/(api/.+)/route\.(js|ts|mjs)$", rel)
        if nm:
            path = "/" + nm.group(2)
            for m in _NEXT_HANDLER.finditer(source):
                line = _line_of(source, m.start())
                rid = self.node(f"route:{rel}#{m.group(1)} {path}", "route", path=rel, symbol=f"{m.group(1)} {path}",
                                language="javascript", meta={"method": m.group(1), "route": path, "line": line})
                self.edge(fid, rid, "defines", _ev(rel, line, m.group(0)))

    def _js_imports(self, rel: str, source: str) -> None:
        fid = file_id(rel)
        is_test = self.nodes[fid].type == "test"
        lines = source.splitlines()
        local_components: Dict[str, str] = {}
        for m in _JS_IMPORT.finditer(source):
            spec = m.group("spec") or m.group("bare") or m.group("req") or m.group("req2") or m.group("dyn")
            clause = m.group("clause") or m.group("req_clause") or ""
            line = _line_of(source, m.start())
            evidence = _ev(rel, line, lines[line - 1] if line <= len(lines) else m.group(0))
            target, how = self._resolve_js(rel, spec)
            if target:
                self.edge(fid, file_id(target), "tests" if is_test else "imports", evidence,
                          "inferred" if how == "inferred" else "established")
                default_name, named = _parse_clause(clause)
                if default_name and target in self.default_export:
                    local_components[default_name] = self.default_export[target]
                for imported, local in named:
                    sid = self.symbols.get(target, {}).get(imported)
                    if sid:
                        self.edge(fid, sid, "uses", evidence)
                        if sid.startswith("component:"):
                            local_components[local] = sid
            elif how == "package":
                name = "/".join(spec.split("/")[:2]) if spec.startswith("@") else spec.split("/")[0]
                if name.startswith("node:") or name in NODE_BUILTINS:
                    continue
                pid = self.node(f"package:{name}", "package", symbol=name, language="javascript")
                self.edge(fid, pid, "depends_on", evidence)
            else:
                self.unresolved.append({"file": rel, "line": line, "module": spec,
                                        "reason": "import path is outside the project" if how == "outside"
                                        else "no project file matches this import"})
        for local, cid in local_components.items():
            m = re.search(rf"<{re.escape(local)}[\s/>]", source)
            if m:
                line = _line_of(source, m.start())
                self.edge(fid, cid, "renders", _ev(rel, line, lines[line - 1]))
        if re.search(r"\bimport\(\s*[^'\"\s)]", source) or re.search(r"\brequire\(\s*[^'\"\s)]", source):
            self.dynamic_imports.append(rel)

    # --- cross-language links ----------------------------------------------------------------------

    def api_calls(self) -> None:
        routes = [n for n in self.nodes.values() if n.type == "route"]
        if not routes:
            return
        for rel, source in self.sources.items():
            if Path(rel).suffix.lower() not in JS_EXT:
                continue
            for m in _JS_API_CALL.finditer(source):
                url = m.group(4)
                if not url.startswith(("/", "http", "${")):
                    continue
                method = (m.group(1) or m.group(2) or "").upper()
                line = _line_of(source, m.start())
                for r in routes:
                    if r.path == rel:
                        continue
                    if routes_match(r.meta.get("route", ""), url) and (not method or r.meta.get("method") in (method, "ANY")):
                        self.edge(file_id(rel), r.id, "calls_api",
                                  _ev(rel, line, f"{m.group(0)}  ~  {r.symbol} in {r.path} (URL pattern match)"),
                                  "inferred")

    def test_conventions(self) -> None:
        """A test named after a module (test_items.py, items.test.js) is linked to it when no import already does."""
        by_stem: Dict[str, List[str]] = {}
        for rel in self.sources:
            if self.nodes.get(file_id(rel)) and self.nodes[file_id(rel)].type == "file":
                by_stem.setdefault(Path(rel).name.split(".")[0], []).append(rel)
        for rel in self.sources:
            if self.nodes.get(file_id(rel), Node(id="", type="")).type != "test":
                continue
            name = Path(rel).name
            stem = re.sub(r"^test_|_test$", "", name.split(".")[0])
            linked = {e.target for e in self.edges.values() if e.source == file_id(rel) and e.type == "tests"}
            candidates = by_stem.get(stem, [])
            if len(candidates) == 1 and file_id(candidates[0]) not in linked:
                self.edge(file_id(rel), file_id(candidates[0]), "tests",
                          f"{rel}: named after {candidates[0]} (naming convention, not an import)", "inferred")

    # --- run -------------------------------------------------------------------------------------------

    def build(self) -> "GraphBuilder":
        self.scan()
        self.python()
        self.javascript()
        if not self.out_of_time():
            self.api_calls()
            self.test_conventions()
        if self.out_of_time():
            self.limits.append(f"analysis stopped at its {self.deadline_seconds:.0f}s time limit; "
                               "some files were not analyzed")
        if self.too_large:
            self.limits.append(f"{len(self.too_large)} file(s) too large to read: {', '.join(self.too_large[:5])}")
        if self.unparseable:
            self.limits.append(f"{len(self.unparseable)} Python file(s) do not parse; their dependencies are unknown")
        if self.dynamic_imports:
            self.limits.append(f"dynamic imports are not followed ({', '.join(self.dynamic_imports[:5])})")
        self.limits.append("routers mounted with a prefix in another file (include_router, app.use) are matched "
                           "to frontend calls by URL suffix, so those links are inferred")
        return self

    def fingerprint(self) -> str:
        return fingerprint_of(self.files)


def _parse_clause(clause: str) -> Tuple[Optional[str], List[Tuple[str, str]]]:
    """`Default, { A, B as C }` -> ('Default', [('A','A'), ('B','C')]); also `{ A: C }` for require."""
    clause = clause.strip()
    default, named = None, []
    brace = re.search(r"\{([^}]*)\}", clause)
    if brace:
        for part in brace.group(1).split(","):
            part = part.strip()
            if not part:
                continue
            m = re.match(r"(\w+)\s*(?:as|:)\s*(\w+)", part)
            named.append((m.group(1), m.group(2)) if m else (part.split()[0], part.split()[0]))
        clause = clause[: brace.start()] + clause[brace.end():]
    rest = clause.strip().strip(",").strip()
    if rest and not rest.startswith("*") and re.match(r"^\w+$", rest):
        default = rest
    return default, named


def fingerprint_of(files: Iterable[Tuple[str, int, int]]) -> str:
    h = hashlib.sha1()
    for rel, size, mtime in sorted(files):
        h.update(f"{rel}|{size}|{mtime}\n".encode())
    return h.hexdigest()


def project_fingerprint(project: Path) -> str:
    files = []
    for rel, path, size in iter_project_files(Path(project).resolve()):
        try:
            files.append((rel, size, path.stat().st_mtime_ns))
        except OSError:
            continue
    return fingerprint_of(files)


def find_cycles(nodes: Iterable[str], edges: Iterable[Tuple[str, str]]) -> List[List[str]]:
    """Strongly connected components with more than one file (Tarjan, iterative)."""
    graph: Dict[str, List[str]] = {n: [] for n in nodes}
    for s, t in edges:
        if s in graph and t in graph:
            graph[s].append(t)
    index, low, on_stack, stack, result = {}, {}, set(), [], []
    counter = [0]
    for start in graph:
        if start in index:
            continue
        work = [(start, iter(graph[start]))]
        index[start] = low[start] = counter[0]
        counter[0] += 1
        stack.append(start)
        on_stack.add(start)
        while work:
            v, it = work[-1]
            advanced = False
            for w in it:
                if w not in index:
                    index[w] = low[w] = counter[0]
                    counter[0] += 1
                    stack.append(w)
                    on_stack.add(w)
                    work.append((w, iter(graph[w])))
                    advanced = True
                    break
                if w in on_stack:
                    low[v] = min(low[v], index[w])
            if advanced:
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[v])
            if low[v] == index[v]:
                comp = []
                while True:
                    w = stack.pop()
                    on_stack.discard(w)
                    comp.append(w)
                    if w == v:
                        break
                if len(comp) > 1:
                    result.append(sorted(comp))
    return sorted(result)


def build_graph(project: Path, deadline_seconds: float = DEFAULT_DEADLINE_SECONDS) -> GraphBuilder:
    return GraphBuilder(project, deadline_seconds).build()
