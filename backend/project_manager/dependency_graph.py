import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("aiforge.project_manager.dependency_graph")

# Pipeline stages and what each depends on (the order the autonomous manager plans in).
DEFAULT_STAGE_DEPENDENCIES: Dict[str, List[str]] = {
    "database": [],
    "backend": ["database"],
    "frontend": ["backend"],
    "testing": ["frontend", "backend"],
    "deployment": ["testing"],
    "documentation": ["deployment"],
}


def _topological_order(adjacency: Dict[str, List[str]]) -> List[str]:
    """Dependencies first. Raises ValueError on a cycle."""
    visited, in_progress, order = set(), set(), []

    def visit(node: str) -> None:
        if node in in_progress:
            raise ValueError(f"Circular dependency detected at '{node}'")
        if node in visited:
            return
        in_progress.add(node)
        for dep in adjacency.get(node, []):
            visit(dep)
        in_progress.discard(node)
        visited.add(node)
        order.append(node)

    for node in adjacency:
        visit(node)
    return order


class ProjectDependencyGraph:
    """
    Task/stage dependency graph: execution order for the autonomous manager's pipeline stages,
    and DAG validation for planned tasks.
    """

    def __init__(self, dependencies: Optional[Dict[str, List[str]]] = None) -> None:
        self.dependencies: Dict[str, List[str]] = {
            k: list(v) for k, v in (dependencies or DEFAULT_STAGE_DEPENDENCIES).items()
        }

    def get_execution_order(self) -> List[str]:
        """Stages ordered so every stage comes after the stages it depends on."""
        return _topological_order(self.dependencies)

    def add_custom_dependency(self, task: str, depends_on: str) -> None:
        self.dependencies.setdefault(task, []).append(depends_on)
        self.dependencies.setdefault(depends_on, [])

    def build_dag(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        adj_list = {t["id"]: list(t.get("dependencies", [])) for t in tasks}
        try:
            order = _topological_order(adj_list)
            has_cycles = False
        except ValueError:
            order, has_cycles = [], True

        logger.info(f"ProjectDependencyGraph built DAG for {len(tasks)} tasks (cycles: {has_cycles}).")
        return {
            "node_count": len(tasks),
            "adjacency_list": adj_list,
            "has_cycles": has_cycles,
            "execution_order": order,
        }


# Global ProjectDependencyGraph Instance
global_project_dependency_graph = ProjectDependencyGraph()

# Backward compatibility alias
DependencyGraph = ProjectDependencyGraph
