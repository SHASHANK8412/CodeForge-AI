"""
AIForge Day 15 — Normalized GraphRepository & Versioning
=========================================================
Stores project engineering graphs with add_node(), add_edge(), traversal methods,
version snapshotting, and graph diffing.
"""

import copy
import logging
from typing import Dict, Any, List, Optional, Set

from backend.dna.models import (
    GraphNode, GraphEdge, EngineeringDNAGraph, NodeKind, RelationType, GraphDiffResult
)

_logger = logging.getLogger("aiforge.dna.repository")


class GraphRepository:
    """
    In-memory and version-aware Graph Repository for Engineering DNA.
    """

    def __init__(self):
        # project_id -> list of EngineeringDNAGraph snapshots
        self._project_snapshots: Dict[str, List[EngineeringDNAGraph]] = {}

    def get_latest_graph(self, project_id: str) -> Optional[EngineeringDNAGraph]:
        snapshots = self._project_snapshots.get(project_id, [])
        return snapshots[-1] if snapshots else None

    def save_graph(self, graph: EngineeringDNAGraph) -> EngineeringDNAGraph:
        if graph.project_id not in self._project_snapshots:
            self._project_snapshots[graph.project_id] = []
        
        version = len(self._project_snapshots[graph.project_id]) + 1
        graph.version = version
        self._project_snapshots[graph.project_id].append(graph)
        _logger.info(f"[GraphRepo] Saved graph version {version} for project '{graph.project_id}' ({len(graph.nodes)} nodes, {len(graph.edges)} edges)")
        return graph

    def get_dependencies(self, project_id: str, node_id: str) -> List[GraphNode]:
        graph = self.get_latest_graph(project_id)
        if not graph:
            return []

        target_ids = {e.target for e in graph.edges if e.source == node_id}
        return [n for n in graph.nodes if n.id in target_ids]

    def get_dependents(self, project_id: str, node_id: str) -> List[GraphNode]:
        graph = self.get_latest_graph(project_id)
        if not graph:
            return []

        source_ids = {e.source for e in graph.edges if e.target == node_id}
        return [n for n in graph.nodes if n.id in source_ids]

    def find_affected_nodes(self, project_id: str, start_node_id: str) -> Set[str]:
        graph = self.get_latest_graph(project_id)
        if not graph:
            return set()

        visited: Set[str] = set()
        queue = [start_node_id]

        while queue:
            curr = queue.pop(0)
            if curr in visited:
                continue
            visited.add(curr)

            # Find all outgoing and incoming connections (transitive impact)
            connected = [
                e.target if e.source == curr else e.source
                for e in graph.edges
                if e.source == curr or e.target == curr
            ]
            for nxt in connected:
                if nxt not in visited:
                    queue.append(nxt)

        return visited

    def diff_graphs(self, project_id: str, v1: int, v2: int) -> GraphDiffResult:
        snapshots = self._project_snapshots.get(project_id, [])
        g1 = next((g for g in snapshots if g.version == v1), None)
        g2 = next((g for g in snapshots if g.version == v2), None)

        if not g1 or not g2:
            return GraphDiffResult(old_version=v1, new_version=v2)

        g1_nodes = {n.id: n for n in g1.nodes}
        g2_nodes = {n.id: n for n in g2.nodes}

        added_nodes = [n for nid, n in g2_nodes.items() if nid not in g1_nodes]
        removed_nodes = [n for nid, n in g1_nodes.items() if nid not in g2_nodes]

        g1_edges = {(e.source, e.target, e.relation): e for e in g1.edges}
        g2_edges = {(e.source, e.target, e.relation): e for e in g2.edges}

        added_edges = [e for key, e in g2_edges.items() if key not in g1_edges]
        removed_edges = [e for key, e in g1_edges.items() if key not in g2_edges]

        risk = "HIGH" if len(added_nodes) + len(removed_nodes) > 5 else "MEDIUM" if len(added_nodes) > 0 else "LOW"

        return GraphDiffResult(
            old_version=v1,
            new_version=v2,
            added_nodes=added_nodes,
            removed_nodes=removed_nodes,
            added_edges=added_edges,
            removed_edges=removed_edges,
            risk_assessment=risk
        )


global_graph_repository = GraphRepository()
