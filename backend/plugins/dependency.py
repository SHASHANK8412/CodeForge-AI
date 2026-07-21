import re
import logging
from typing import Dict, Any, List, Set, Tuple

_logger = logging.getLogger("aiforge.plugins")

class DependencyException(Exception):
    pass

class DependencyResolver:
    """
    Validates semantic version constraints and checks for circular dependencies.
    """

    def __init__(self) -> None:
        pass

    def parse_semver(self, dep_string: str) -> Tuple[str, str, str]:
        """
        Parses package strings (e.g. 'AuthPlugin>=1.2.0') into (name, operator, version).
        """
        match = re.match(r'^([a-zA-Z0-9_\-]+)\s*(>=|==|<=|>|<|)?\s*([0-9\.]+)?$', dep_string.strip())
        if not match:
            return dep_string, "", ""
        return match.group(1), match.group(2) or "", match.group(3) or ""

    def check_circular_dependencies(self, dep_graph: Dict[str, List[str]]) -> List[str]:
        """
        Performs topological sort to find resolving order and detect circular loops.
        """
        visited: Set[str] = set()
        stack: Set[str] = set()
        order: List[str] = []

        def dfs(node: str) -> None:
            if node in stack:
                raise DependencyException(f"Circular Dependency Detected: cycle loops on '{node}'")
            if node not in visited:
                stack.add(node)
                # Resolve dep nodes
                deps = dep_graph.get(node, [])
                for dep in deps:
                    name, _, _ = self.parse_semver(dep)
                    # Recurse if dependency name is present in graphs
                    if name in dep_graph:
                        dfs(name)
                stack.remove(node)
                visited.add(node)
                order.append(node)

        for n in dep_graph:
            if n not in visited:
                dfs(n)

        return order

    def matches_version(self, available_version: str, operator: str, required_version: str) -> bool:
        """
        Validates basic semantic version comparisons.
        """
        if not operator or not required_version:
            return True

        try:
            v_avail = [int(x) for x in available_version.split(".")]
            v_req = [int(x) for x in required_version.split(".")]
            
            # Align length
            max_len = max(len(v_avail), len(v_req))
            v_avail.extend([0] * (max_len - len(v_avail)))
            v_req.extend([0] * (max_len - len(v_req)))

            if operator == "==":
                return v_avail == v_req
            elif operator == ">=":
                return v_avail >= v_req
            elif operator == "<=":
                return v_avail <= v_req
            elif operator == ">":
                return v_avail > v_req
            elif operator == "<":
                return v_avail < v_req
        except Exception:
            return False
        return True
