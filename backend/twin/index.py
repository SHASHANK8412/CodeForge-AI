"""Queries over a stored dependency graph: file-level dependencies and dependents, neighborhoods."""

from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from backend.twin.models import Edge, GraphAnalysis, Node

# Edge types along which a change can propagate from a target to whatever points at it.
DEPENDENCY_EDGES = {"imports", "uses", "renders", "calls_api", "tests"}


_SPECIFICITY = {"renders": 0, "uses": 1, "calls_api": 2, "tests": 3, "imports": 4}


def _better(edge: Edge, current: Edge) -> bool:
    """Established beats inferred; then the more specific relationship (renders > uses > ... > imports)."""
    if edge.certainty != current.certainty:
        return edge.certainty == "established"
    return _SPECIFICITY.get(edge.type, 9) < _SPECIFICITY.get(current.type, 9)


class GraphIndex:
    def __init__(self, graph: GraphAnalysis):
        self.graph = graph
        self.nodes: Dict[str, Node] = {n.id: n for n in graph.nodes}
        self.out: Dict[str, List[Edge]] = {}
        self.inc: Dict[str, List[Edge]] = {}
        for e in graph.edges:
            self.out.setdefault(e.source, []).append(e)
            self.inc.setdefault(e.target, []).append(e)
        self.files = {n.path for n in graph.nodes if n.type in ("file", "test", "config") and n.path}

    def file_of(self, node_id: str) -> Optional[str]:
        n = self.nodes.get(node_id)
        return n.path if n is not None else None

    def node_type(self, path: str) -> str:
        n = self.nodes.get(f"file:{path}")
        return n.type if n else "unknown"

    def defined_in(self, path: str, types: Tuple[str, ...]) -> List[Node]:
        return [self.nodes[e.target] for e in self.out.get(f"file:{path}", [])
                if e.type == "defines" and self.nodes.get(e.target) and self.nodes[e.target].type in types]

    def dependents(self, path: str) -> List[Tuple[str, Edge]]:
        """(file, edge) for every file with a dependency edge into `path` or into a symbol defined in it."""
        targets = [f"file:{path}"] + [n.id for n in self.defined_in(path, ("function", "class", "model", "component", "route"))]
        found: Dict[str, Edge] = {}
        for t in targets:
            for e in self.inc.get(t, []):
                if e.type not in DEPENDENCY_EDGES:
                    continue
                src = self.file_of(e.source)
                if not src or src == path:
                    continue
                if src not in found or _better(e, found[src]):
                    found[src] = e
        return sorted(found.items())

    def dependencies(self, path: str) -> List[Tuple[str, Edge]]:
        found: Dict[str, Edge] = {}
        for e in self.out.get(f"file:{path}", []):
            if e.type not in DEPENDENCY_EDGES:
                continue
            tgt = self.file_of(e.target)
            if not tgt or tgt == path:
                continue
            if tgt not in found or _better(e, found[tgt]):
                found[tgt] = e
        return sorted(found.items())

    def reverse_closure(self, seeds: List[str], max_depth: int = 4) -> Dict[str, Dict]:
        """
        Files that depend on the seeds, directly (depth 1) or through other files, with the chain
        that connects them and whether every link in it is established.
        """
        seen: Dict[str, Dict] = {}
        queue = deque((s, 0, [s], True) for s in seeds)
        seed_set = set(seeds)
        while queue:
            path, depth, chain, established = queue.popleft()
            if depth >= max_depth:
                continue
            for dep, edge in self.dependents(path):
                if dep in seed_set:
                    continue
                ok = established and edge.certainty == "established"
                current = seen.get(dep)
                if current is not None and (current["depth"] < depth + 1 or
                                            (current["depth"] == depth + 1 and current["established"] >= ok)):
                    continue
                seen[dep] = {"path": dep, "depth": depth + 1, "chain": chain + [dep], "established": ok,
                             "via": edge.type, "evidence": edge.evidence}
                queue.append((dep, depth + 1, chain + [dep], ok))
        return seen

    def neighborhood(self, node_id: str, depth: int = 2, direction: str = "both", limit: int = 150
                     ) -> Tuple[List[Node], List[Edge], Dict[str, int]]:
        """Nodes within `depth` hops of `node_id` (all edge types), with each node's distance."""
        if node_id not in self.nodes:
            return [], [], {}
        dist = {node_id: 0}
        queue = deque([node_id])
        while queue and len(dist) < limit:
            cur = queue.popleft()
            if dist[cur] >= depth:
                continue
            nxt: List[str] = []
            if direction in ("both", "out"):
                nxt += [e.target for e in self.out.get(cur, [])]
            if direction in ("both", "in"):
                nxt += [e.source for e in self.inc.get(cur, [])]
            for n in nxt:
                if n not in dist and len(dist) < limit:
                    dist[n] = dist[cur] + 1
                    queue.append(n)
        ids: Set[str] = set(dist)
        edges = [e for e in self.graph.edges if e.source in ids and e.target in ids]
        return [self.nodes[i] for i in ids], edges, dist
