"""
Change impact analysis: which files a proposed change targets, what depends on them, and which
APIs, models, components, configuration and interfaces are involved.

The targets ("seeds") come from up to three sources, each recorded on the seed:
  * files the user picked
  * the planner model's structured proposal, validated against the graph (optional)
  * keyword matching of the request against file paths, symbols, routes and models
Everything after the seeds is computed from the graph with fixed rules; no model decides
what depends on what.
"""

import json
import re
from typing import Any, Callable, Dict, List, Tuple

from backend.twin.index import GraphIndex
from backend.twin.models import Prediction

MAX_SEEDS = 8
MAX_DEPTH = 4
_STOP = {"the", "and", "for", "with", "without", "add", "new", "make", "use", "using", "into", "from", "that", "this",
         "should", "must", "can", "all", "existing", "change", "update", "modify", "support", "allow", "users", "user's",
         "breaking", "please", "want", "need", "also", "file", "files", "code", "feature", "app", "application", "via",
         "able", "when", "will", "not", "but", "any", "our", "their", "its", "them", "then", "than", "more", "less"}
_KINDS = {
    "auth": r"\b(auth\w*|log ?in|logout|sign ?(in|up)|password|token|jwt|oauth|session|permission|role|sso|google login)\b",
    "database": r"\b(database|db|schema|table|column|migration|model|sql\w*|orm|mongo\w*|index)\b",
    "public_api": r"\b(endpoint|api|route|rest|response|request|status code|graphql)\b",
    "frontend_ui": r"\b(page|component|button|form|ui|screen|view|modal|layout|css|style|react)\b",
    "dependency": r"\b(install|upgrade|library|package|dependency|sdk|npm|pip)\b",
    "configuration": r"\b(config\w*|setting|env|environment variable|secret|cors|port)\b",
    "tests": r"\b(tests?|coverage|pytest|jest)\b",
}
PLANNER_SYSTEM = (
    "You map a change request onto an existing project. Answer with JSON only: "
    '{"modify": [existing file paths], "create": [new file paths], "change_kinds": [...], "notes": "..."}. '
    "Use only paths from the provided list for \"modify\". change_kinds may contain: auth, database, public_api, "
    "frontend_ui, dependency, configuration, tests."
)


def _tokens(text: str) -> List[str]:
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    return [t for t in re.split(r"[^a-zA-Z0-9]+", text.lower()) if len(t) >= 3 and t not in _STOP]


def _stem(word: str) -> str:
    for suffix in ("ication", "ations", "ation", "ings", "ing", "ers", "ies", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def keyword_seeds(index: GraphIndex, request: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Files whose path, symbols, routes or models share words with the request. Returns (seeds, unmatched words)."""
    words = {_stem(w) for w in _tokens(request)}
    if not words:
        return [], []
    scores: Dict[str, float] = {}
    reasons: Dict[str, set] = {}
    matched = set()

    def hit(path: str, points: float, word: str, what: str):
        scores[path] = scores.get(path, 0) + points
        reasons.setdefault(path, set()).add(f"'{word}' in {what}")
        matched.add(word)

    for node in index.nodes.values():
        if not node.path or index.node_type(node.path) in ("test", "config", "unknown"):
            continue
        if node.type == "file":
            parts = node.path.lower().split("/")
            stem_words = {_stem(t) for t in _tokens(parts[-1].rsplit(".", 1)[0])}
            dir_words = {_stem(t) for p in parts[:-1] for t in _tokens(p)}
            for w in words & stem_words:
                hit(node.path, 3, w, "file name")
            for w in words & dir_words:
                hit(node.path, 1, w, "folder")
        elif node.type in ("function", "class", "model", "component") and node.symbol:
            sym = {_stem(t) for t in _tokens(node.symbol)}
            for w in words & sym:
                hit(node.path, 3 if node.type in ("model", "component") else 2, w, f"{node.type} {node.symbol}")
        elif node.type == "route":
            segs = {_stem(t) for t in _tokens(node.meta.get("route", ""))}
            for w in words & segs:
                hit(node.path, 2, w, f"route {node.symbol}")
    if not scores:
        return [], sorted(words)
    best = max(scores.values())
    chosen = sorted((p for p, s in scores.items() if s >= 3 and s >= best * 0.5), key=lambda p: (-scores[p], p))
    seeds = [{"path": p, "source": "keyword match", "certainty": "inferred",
              "reason": "; ".join(sorted(reasons[p])), "score": scores[p]} for p in chosen[:MAX_SEEDS]]
    return seeds, sorted(words - matched)


def planner_proposal(index: GraphIndex, request: str, generate: Callable[[str, str], str]
                     ) -> Tuple[List[Dict[str, Any]], List[str], List[str], str]:
    """(modify seeds, create paths, change kinds, notes) from the planner model, validated against the graph."""
    from backend.exporter.zipper import export_exclusion_reason
    files = sorted(p for p in index.files if index.node_type(p) != "config")[:400]
    routes = [n.symbol for n in index.nodes.values() if n.type == "route"][:80]
    models = [f"{n.symbol} ({n.path})" for n in index.nodes.values() if n.type == "model"][:60]
    prompt = (f"Change request: {request}\n\nProject files:\n" + "\n".join(files)
              + ("\n\nRoutes: " + ", ".join(routes) if routes else "")
              + ("\nModels: " + ", ".join(models) if models else ""))
    reply = generate(PLANNER_SYSTEM, prompt)
    match = re.search(r"\{.*\}", reply or "", re.S)
    data = json.loads(match.group(0)) if match else {}
    seeds, notes = [], str(data.get("notes") or "")[:500]
    unknown = []
    for p in data.get("modify") or []:
        p = _clean_path(p)
        if p in index.files:
            seeds.append({"path": p, "source": "planner model", "certainty": "inferred",
                          "reason": "proposed by the planner model; the path exists in the project"})
        else:
            unknown.append(p)
    create = []
    for p in data.get("create") or []:
        p = _clean_path(p)
        if p and ".." not in p.split("/") and not p.startswith("/") and not export_exclusion_reason(p) and p not in index.files:
            create.append(p)
    if unknown:
        notes = (notes + " " if notes else "") + f"[proposed paths that do not exist and were ignored: {', '.join(unknown[:5])}]"
    kinds = [k for k in (data.get("change_kinds") or []) if k in _KINDS]
    return seeds[:MAX_SEEDS], create[:10], kinds, notes


def _clean_path(p: Any) -> str:
    """A relative project path, or '' for anything absolute or climbing out of the project."""
    p = str(p).strip().replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    if not p or p.startswith("/") or re.match(r"^[A-Za-z]:", p) or ".." in p.split("/"):
        return ""
    return p


def change_kinds(request: str, index: GraphIndex, seeds: List[str]) -> List[str]:
    text = request.lower()
    kinds = {k for k, pattern in _KINDS.items() if re.search(pattern, text)}
    for p in seeds:
        if index.defined_in(p, ("route",)):
            kinds.add("public_api")
        if any(n.meta.get("kind") == "orm" for n in index.defined_in(p, ("model",))):
            kinds.add("database")
        if index.defined_in(p, ("component",)) or p.endswith((".jsx", ".tsx")):
            kinds.add("frontend_ui")
        if re.search(r"(^|/)(auth|security|login|token|jwt|session|permissions?)\w*\.(py|js|ts|jsx|tsx)$", p):
            kinds.add("auth")
    return sorted(kinds)


def predict(index: GraphIndex, request: str, label: str, seeds: List[Dict[str, Any]], create: List[str],
            kinds: List[str]) -> Prediction:
    seed_paths = [s["path"] for s in seeds]
    closure = index.reverse_closure(seed_paths, MAX_DEPTH)
    affected = {p: v for p, v in closure.items() if index.node_type(p) != "test"}
    direct = [{"path": p, "via": v["via"], "evidence": v["evidence"],
               "certainty": "established" if v["established"] else "inferred"}
              for p, v in sorted(affected.items()) if v["depth"] == 1]
    transitive = [{"path": p, "depth": v["depth"], "chain": v["chain"],
                   "certainty": "established" if v["established"] else "inferred"}
                  for p, v in sorted(affected.items(), key=lambda kv: (kv[1]["depth"], kv[0])) if v["depth"] > 1]
    scope_and_affected = seed_paths + list(affected)

    apis, seen_routes = [], set()
    for p in scope_and_affected:
        for r in index.defined_in(p, ("route",)):
            if r.id in seen_routes:
                continue
            seen_routes.add(r.id)
            callers = sorted({index.file_of(e.source) for e in index.inc.get(r.id, []) if e.type == "calls_api"} - {None})
            relation = ("defined in a file the change modifies" if p in seed_paths else
                        f"its file depends on the change (depth {affected[p]['depth']})")
            apis.append({"route": r.symbol, "file": p, "relation": relation, "frontend_callers": callers,
                         "certainty": "established" if p in seed_paths or affected[p]["established"] else "inferred"})

    models, seen_models = [], set()
    for p in seed_paths:
        for m in index.defined_in(p, ("model",)):
            seen_models.add(m.id)
            models.append({"model": m.symbol, "file": p, "kind": m.meta.get("kind"), "relation": "defined in a modified file"})
    for p in seed_paths:
        for e in index.out.get(f"file:{p}", []):
            n = index.nodes.get(e.target)
            if e.type == "uses" and n is not None and n.type == "model" and n.id not in seen_models:
                seen_models.add(n.id)
                models.append({"model": n.symbol, "file": n.path, "kind": n.meta.get("kind"),
                               "relation": f"used by {p}"})

    components = []
    for p in scope_and_affected:
        for c in index.defined_in(p, ("component",)):
            renderers = sorted({index.file_of(e.source) for e in index.inc.get(c.id, []) if e.type == "renders"} - {None})
            components.append({"component": c.symbol, "file": p, "rendered_by": renderers,
                               "relation": "in a modified file" if p in seed_paths else "depends on the change"})

    configs = []
    config_nodes = [n for n in index.nodes.values() if n.type == "config" or (n.type == "file" and n.meta.get("config"))]
    for n in config_nodes:
        name = n.path.rsplit("/", 1)[-1]
        reason = None
        if "dependency" in kinds and name in ("requirements.txt", "package.json", "pyproject.toml"):
            reason = "the change adds or changes dependencies"
        elif {"auth", "configuration"} & set(kinds) and (name.startswith(".env") or n.meta.get("config")):
            reason = "authentication/configuration changes usually need new settings"
        elif "database" in kinds and (name.startswith(".env") or n.meta.get("config") or "docker-compose" in name):
            reason = "database settings"
        elif n.type == "file" and n.path in scope_and_affected:
            reason = "a settings module in the affected area"
        if reason:
            configs.append({"file": n.path, "reason": reason, "certainty": "inferred"})

    interfaces = []
    for p in seed_paths:
        for sym in index.defined_in(p, ("function", "class", "model", "component", "route")):
            users = sorted({index.file_of(e.source) for e in index.inc.get(sym.id, [])
                            if e.type in ("uses", "renders", "calls_api")} - {None, p})
            if users:
                interfaces.append({"symbol": sym.symbol, "type": sym.type, "file": p, "used_by": users,
                                   "note": "changing its name, parameters or return shape breaks these callers"})
    interfaces.sort(key=lambda i: -len(i["used_by"]))

    create_dirs = sorted({c.rsplit("/", 1)[0] + "/" if "/" in c else "./" for c in create})
    return Prediction(label=label, request=request, seeds=seeds, change_kinds=kinds, modify_scope=sorted(seed_paths),
                      create_scope=create_dirs, direct=direct, transitive=transitive, apis=apis, models=models,
                      components=components, configs=configs, interfaces_at_risk=interfaces[:40])
