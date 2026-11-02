"""
Every key a pipeline node writes or reads must be declared in ProjectState.

LangGraph silently drops undeclared keys from node results and from the initial input. That is
how session_id, deployment_status, health_status, zip_path and others vanished: the health check
then probed AIForge's own API and reported the generated app HEALTHY.
"""
import ast
from pathlib import Path

from backend.graph.project_state import ProjectState

SOURCE = Path(__file__).resolve().parents[1] / "backend" / "graph" / "parallel_workflow.py"


def _node_keys():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    written, read = {}, {}
    for fn in tree.body:
        if not isinstance(fn, (ast.AsyncFunctionDef, ast.FunctionDef)):
            continue
        for node in ast.walk(fn):
            if fn.name.endswith("_node") and isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
                for key in node.value.keys:
                    if isinstance(key, ast.Constant):
                        written.setdefault(key.value, set()).add(fn.name)
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get"
                    and isinstance(node.func.value, ast.Name) and node.func.value.id == "state"
                    and node.args and isinstance(node.args[0], ast.Constant)):
                read.setdefault(node.args[0].value, set()).add(fn.name)
    return written, read


def test_every_node_key_is_declared():
    declared = set(ProjectState.__annotations__)
    written, read = _node_keys()
    assert {k: sorted(v) for k, v in written.items() if k not in declared} == {}
    assert {k: sorted(v) for k, v in read.items() if k not in declared} == {}


def test_routers_do_not_write_state():
    """A conditional-edge function's writes are discarded; decisions that must persist belong
    in a node's result (see repair_escalation / final_approval_node)."""
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    offenders = []
    for fn in tree.body:
        if isinstance(fn, ast.FunctionDef) and fn.name.startswith("route_"):
            for node in ast.walk(fn):
                if isinstance(node, ast.Assign) and any(
                        isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) and t.value.id == "state"
                        for t in node.targets):
                    offenders.append(fn.name)
    assert offenders == []
