import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.project_manager")

class DependencyGraph:
    """
    Builds project task dependency maps dynamically to guide safe orchestrations.
    """

    def __init__(self) -> None:
        self.dependencies: Dict[str, List[str]] = {
            "database": [],
            "backend": ["database"],
            "frontend": ["backend"],
            "testing": ["frontend", "backend"],
            "deployment": ["testing"],
            "documentation": ["deployment"]
        }

    def get_execution_order(self) -> List[str]:
        """
        Calculates execution ordering using simple topological sort.
        """
        visited = set()
        stack = set()
        order = []

        def dfs(node: str) -> None:
            if node in stack:
                raise ValueError(f"Circular dependency cycle detected: {node}")
            if node not in visited:
                stack.add(node)
                for dep in self.dependencies.get(node, []):
                    dfs(dep)
                stack.remove(node)
                visited.add(node)
                order.append(node)

        # Force sort across configured dependency keys
        for k in self.dependencies:
            dfs(k)

        return order

    def add_custom_dependency(self, task: str, depends_on: str) -> None:
        self.dependencies.setdefault(task, []).append(depends_on)
