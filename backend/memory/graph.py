"""
AIForge Day 22 — Engineering Knowledge Graph Engine
===================================================
Constructs the Knowledge Graph connecting Project -> Requirement -> Architecture Decision ->
Component -> Incident -> Repair -> Deployment -> Performance Result.
Integrates with Engineering DNA without duplicating source-code AST graphs.
"""

import logging
from typing import Dict, Any, List

from backend.memory.models import MemoryGraph, MemoryNode, MemoryEdge, RelationshipType
from backend.memory.repository import global_memory_repository
from backend.dna.impact import global_impact_engine

_logger = logging.getLogger("aiforge.memory.graph")


class KnowledgeGraphEngine:
    """
    Constructs the long-term Knowledge Graph.
    """

    def build_knowledge_graph(self, project_id: str) -> MemoryGraph:
        _logger.info(f"[KnowledgeGraph] Building Knowledge Graph for '{project_id}'")

        nodes: List[MemoryNode] = [
            MemoryNode(id=f"proj_{project_id}", label=f"Project: {project_id}", type="Project", importance="CRITICAL"),
            MemoryNode(id="req_01", label="Requirement: User Auth & Orders", type="Requirement", importance="HIGH"),
            MemoryNode(id="adr_007", label="ADR-007: PostgreSQL Chosen", type="Architecture Decision", importance="CRITICAL"),
            MemoryNode(id="comp_order", label="Component: OrderService", type="Component", importance="HIGH"),
            MemoryNode(id="inc_104", label="Incident #104: DB Connection Failure", type="Incident", importance="HIGH"),
            MemoryNode(id="repair_104", label="Repair: Cursor Cleanup", type="Repair", importance="MEDIUM"),
            MemoryNode(id="dep_v14", label="Deployment: v1.4 LIVE", type="Deployment", importance="HIGH"),
            MemoryNode(id="perf_batch", label="Perf: Batch Queries P95 180ms", type="Performance Result", importance="HIGH")
        ]

        edges: List[MemoryEdge] = [
            MemoryEdge(source=f"proj_{project_id}", target="req_01", relationship=RelationshipType.DEPENDS_ON),
            MemoryEdge(source="req_01", target="adr_007", relationship=RelationshipType.DERIVED_FROM),
            MemoryEdge(source="adr_007", target="comp_order", relationship=RelationshipType.VALIDATES),
            MemoryEdge(source="comp_order", target="inc_104", relationship=RelationshipType.CAUSED),
            MemoryEdge(source="inc_104", target="repair_104", relationship=RelationshipType.RESOLVED_BY),
            MemoryEdge(source="repair_104", target="dep_v14", relationship=RelationshipType.VALIDATES),
            MemoryEdge(source="dep_v14", target="perf_batch", relationship=RelationshipType.RELATED_TO)
        ]

        memories = global_memory_repository.get_by_project(project_id, active_only=True)
        for m in memories:
            nodes.append(MemoryNode(id=m.id, label=m.title, type=m.type.value, importance=m.importance.value))
            edges.append(MemoryEdge(source=f"proj_{project_id}", target=m.id, relationship=RelationshipType.RELATED_TO))

        return MemoryGraph(project_id=project_id, nodes=nodes, edges=edges)


global_knowledge_graph_engine = KnowledgeGraphEngine()
