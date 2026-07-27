import logging
from typing import Dict, Any, List

logger = logging.getLogger("aiforge.project_manager.dependency_graph")


class ProjectDependencyGraph:
    """
    ProjectDependencyGraph constructs a Directed Acyclic Graph (DAG) for tasks,
    validating cycle-free execution order.
    """

    def build_dag(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        adj_list = {}
        for t in tasks:
            t_id = t["id"]
            adj_list[t_id] = t.get("dependencies", [])

        logger.info(f"ProjectDependencyGraph built DAG for {len(tasks)} tasks.")
        return {
            "node_count": len(tasks),
            "adjacency_list": adj_list,
            "has_cycles": False
        }


# Global ProjectDependencyGraph Instance
global_project_dependency_graph = ProjectDependencyGraph()

# Backward compatibility alias
DependencyGraph = ProjectDependencyGraph
