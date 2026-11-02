"""
Risk assessment and test selection for a predicted change.

Risk is a sum of points from fixed rules (each listed with its reason), mapped to a category:
  0-3 low, 4-7 medium, 8-11 high, 12+ critical; authentication changes are at least "high"
  and always need a security review. It is a heuristic ranking for review effort, not a
  measured probability of failure.
"""

from typing import Any, Dict, List, Optional

from backend.twin.index import GraphIndex
from backend.twin.models import Prediction, RiskFactor, SelectedTest

CATEGORIES = ((12, "critical"), (8, "high"), (4, "medium"), (0, "low"))
BROAD_REGRESSION_AFFECTED = 10


def assess(pred: Prediction, index: GraphIndex, history: Optional[Dict[str, Any]] = None) -> None:
    history = history or {}
    factors: List[RiskFactor] = []

    def add(name: str, points: int, reason: str):
        if points:
            factors.append(RiskFactor(factor=name, points=points, reason=reason))

    affected = len(pred.direct) + len(pred.transitive)
    add("affected files", 3 if affected >= 15 else 2 if affected >= 6 else 1 if affected >= 2 else 0,
        f"{affected} file(s) depend on the changed files")
    depth = max((t["depth"] for t in pred.transitive), default=1 if pred.direct else 0)
    add("dependency depth", 2 if depth >= 3 else 1 if depth == 2 else 0, f"changes propagate {depth} level(s) deep")

    hubs = [i for i in pred.interfaces_at_risk if len(i["used_by"]) >= 5]
    entry = [p for p in pred.modify_scope if _is_entry(index, p)]
    add("critical modules", min(2, len(hubs)) + (1 if entry else 0),
        "; ".join(([f"{len(hubs)} symbol(s) used by 5+ files"] if hubs else []) +
                  ([f"entry point(s) modified: {', '.join(entry)}"] if entry else [])) or "-")
    if any(a["relation"].startswith("defined in a file the change modifies") for a in pred.apis):
        add("public API", 2, "the change modifies files that define HTTP routes")
    if "database" in pred.change_kinds or any(m["kind"] == "orm" and m["relation"].startswith("defined") for m in pred.models):
        add("database schema", 2, "database models or schema may change (migrations, existing data)")
    if "auth" in pred.change_kinds:
        add("authentication/authorization", 3, "the change touches login, tokens or permissions")
        pred.security_review = True

    tested = {t.path for t in pred.tests}
    untested_scope = [p for p in pred.modify_scope if p in pred.untested]
    if pred.modify_scope:
        share = len(untested_scope) / len(pred.modify_scope)
        add("test coverage", 2 if share > 0.5 else 1 if share > 0 else 0,
            f"{len(untested_scope)} of {len(pred.modify_scope)} changed file(s) have no associated test"
            + ("" if tested else "; no tests were found for the affected area"))
    failing = history.get("failing_files") or []
    hit = sorted(set(failing) & set(pred.modify_scope + [d["path"] for d in pred.direct]))
    add("previous validation failures", min(2, len(hit)),
        f"open Autopilot findings (syntax/quality/test failures) in: {', '.join(hit)}" if hit else "-")

    inferred = [d for d in pred.direct + pred.transitive if d["certainty"] == "inferred"]
    seeds_inferred = all(s.get("certainty") == "inferred" for s in pred.seeds)
    uncertain = (1 if inferred and len(inferred) * 2 >= max(1, affected) else 0) + (1 if seeds_inferred or not pred.seeds else 0)
    add("uncertainty", uncertain,
        "; ".join(([f"{len(inferred)} of {affected} dependent file(s) linked by inferred edges"] if inferred else []) +
                  (["no file could be identified as the change target"] if not pred.seeds else
                   ["the target files were found by keyword/model matching, not chosen explicitly"] if seeds_inferred else [])) or "-")

    points = sum(f.points for f in factors)
    category = next(name for threshold, name in CATEGORIES if points >= threshold)
    if pred.security_review and category in ("low", "medium"):
        category = "high"
        factors.append(RiskFactor(factor="security floor", points=0,
                                  reason="authentication changes are rated at least high and need a security review"))
    pred.risk, pred.risk_points, pred.risk_factors = category, points, factors


def _is_entry(index: GraphIndex, path: str) -> bool:
    node = index.nodes.get(f"file:{path}")
    return bool(node is not None and node.meta.get("entry")) or path.rsplit("/", 1)[-1] in (
        "main.py", "app.py", "server.js", "app.js", "main.jsx", "main.tsx", "manage.py")


def select_tests(pred: Prediction, index: GraphIndex) -> None:
    """Tests linked to the changed and dependent files, integration tests for affected APIs, and the
    whole suite when the impact is broad. Each test lists why it was chosen."""
    tests: Dict[str, SelectedTest] = {}
    all_tests = sorted(p for p in index.files if index.node_type(p) == "test")

    def add(path: str, reason: str, certainty: str, kind: str):
        t = tests.get(path)
        if t is None:
            tests[path] = SelectedTest(path=path, reasons=[reason], certainty=certainty, kind=kind)
        else:
            if reason not in t.reasons:
                t.reasons.append(reason)
            if certainty == "established":
                t.certainty = "established"

    covered = set()
    for p in pred.modify_scope:
        for src, edge in index.dependents(p):
            if index.node_type(src) == "test":
                add(src, f"{'imports' if edge.certainty == 'established' else 'is named after'} {p} (a changed file)",
                    edge.certainty, "unit")
                covered.add(p)
    for d in pred.direct + pred.transitive:
        for src, edge in index.dependents(d["path"]):
            if index.node_type(src) == "test":
                add(src, f"covers {d['path']}, which depends on the change", edge.certainty, "unit")
    route_paths = {a["route"].split(" ", 1)[-1] for a in pred.apis}
    for t in all_tests:
        source = _read_test(index, t)
        if source is None:
            continue
        if ("TestClient" in source or "supertest" in source or "request(app" in source) and route_paths:
            hits = sorted(r for r in route_paths if r and r.split("{")[0].split(":")[0].rstrip("/") in source)
            if hits:
                add(t, f"integration test calling affected route(s): {', '.join(hits[:4])}", "inferred", "integration")
    affected = len(pred.direct) + len(pred.transitive)
    if affected >= BROAD_REGRESSION_AFFECTED or pred.risk in ("high", "critical"):
        for t in all_tests:
            add(t, f"broad regression run: {affected} dependent files / risk {pred.risk}", "established", "regression")
    pred.tests = sorted(tests.values(), key=lambda t: ({"unit": 0, "integration": 1, "regression": 2}[t.kind], t.path))
    pred.untested = sorted(p for p in pred.modify_scope if p not in covered and index.node_type(p) != "config")


def _read_test(index: GraphIndex, path: str) -> Optional[str]:
    root = getattr(index, "project_root", None)
    if root is None:
        return None
    try:
        return (root / path).read_text(encoding="utf-8")[:200_000]
    except (OSError, UnicodeDecodeError):
        return None


def validation_steps(pred: Prediction, tooling: Dict[str, bool]) -> None:
    steps = ["Run the Python syntax check and the code-quality gate (blocking errors must not increase)."]
    if pred.tests:
        steps.append(f"Run the {len(pred.tests)} selected test file(s) "
                     + ("in the Docker sandbox." if tooling.get("docker") else
                        "- Docker is not available, so tests cannot run here; the result would rest on static checks."))
    else:
        steps.append("No tests cover the changed files: add tests for them before relying on the change.")
    if pred.interfaces_at_risk:
        steps.append(f"Check the callers of {len(pred.interfaces_at_risk)} changed interface(s) "
                     f"(e.g. {pred.interfaces_at_risk[0]['symbol']} used by {len(pred.interfaces_at_risk[0]['used_by'])} file(s)).")
    if "database" in pred.change_kinds:
        steps.append("Review model/schema changes and plan a migration for existing data.")
    if pred.security_review:
        steps.append("Security review of the authentication change (token handling, password storage, access checks).")
    if any(a["frontend_callers"] for a in pred.apis):
        steps.append("Check the frontend callers of the affected routes still match request and response shapes.")
    if "frontend_ui" in pred.change_kinds:
        steps.append("Build the frontend and check the affected components render" +
                     ("" if tooling.get("oxlint") else " (oxlint is not available for the JS lint step)") + ".")
    if "dependency" in pred.change_kinds:
        steps.append("Install dependencies from scratch and run the dependency audit.")
    steps.append("Static security scan (Bandit) must not report new high-severity issues.")
    pred.validation_steps = steps
