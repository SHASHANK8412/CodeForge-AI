import logging
from typing import List, Dict, Any
from backend.knowledge.graph.knowledge_graph import KnowledgeGraph

_logger = logging.getLogger("aiforge.knowledge")

class GraphBuilder:
    """
    Builds and populates the technology relationships graph while enforcing cycle checks (DAG parameters).
    """

    def __init__(self, graph: KnowledgeGraph) -> None:
        self.graph = graph

    def add_relationship(self, source: str, target: str, relation: str = "uses") -> bool:
        """
        Adds relationship edge source -> target after running cycle detection.
        """
        s_clean = source.lower().strip()
        t_clean = target.lower().strip()

        # 1. Check if path from target back to source already exists (cycle check)
        if self._has_path(t_clean, s_clean):
            _logger.warning(f"Cycle prevention: Skip adding edge '{s_clean}' -> '{t_clean}' to preserve DAG constraints.")
            return False

        self.graph.add_edge(s_clean, t_clean, relation)
        return True

    def _has_path(self, start: str, end: str, visited: set = None) -> bool:
        """
        BFS/DFS helper search path between start and end.
        """
        if start == end:
            return True
        if visited is None:
            visited = set()

        visited.add(start)
        neighbors = self.graph.get_neighbors(start)
        
        for n in neighbors:
            target_node = n["target"]
            if target_node not in visited:
                if self._has_path(target_node, end, visited):
                    return True
        return False
