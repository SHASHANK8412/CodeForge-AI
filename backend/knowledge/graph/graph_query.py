import logging
from typing import List, Dict, Any, Set
from collections import deque
from backend.knowledge.graph.knowledge_graph import KnowledgeGraph

_logger = logging.getLogger("aiforge.knowledge")

class GraphQuery:
    """
    Exposes graph query operations: BFS traversals, shortest path routing, and dependency lookup.
    """

    def __init__(self, graph: KnowledgeGraph) -> None:
        self.graph = graph

    def traverse_graph(self, start_node: str) -> List[str]:
        """
        BFS traversal returning visited nodes list.
        """
        start = start_node.lower().strip()
        visited: Set[str] = set()
        queue = deque([start])
        path = []

        while queue:
            node = queue.popleft()
            if node not in visited:
                visited.add(node)
                path.append(node)
                # Query neighbors
                for neighbor in self.graph.get_neighbors(node):
                    queue.append(neighbor["target"])

        return path

    def shortest_path(self, start_node: str, end_node: str) -> List[str]:
        """
        Calculates shortest path using BFS. Returns list of nodes in path or empty list.
        """
        start = start_node.lower().strip()
        end = end_node.lower().strip()

        if start == end:
            return [start]

        visited: Set[str] = {start}
        queue = deque([[start]])

        while queue:
            path = queue.popleft()
            node = path[-1]

            for neighbor in self.graph.get_neighbors(node):
                target = neighbor["target"]
                if target == end:
                    return path + [target]
                
                if target not in visited:
                    visited.add(target)
                    queue.append(path + [target])

        return []

    def get_dependencies_deep(self, node: str) -> List[str]:
        """
        Recursively fetches all downstream dependent technologies.
        """
        return self.traverse_graph(node)[1:]
