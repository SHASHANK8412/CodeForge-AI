"""
AIForge Knowledge Graph Builder
================================
Constructs, links, and queries the project Knowledge Graph mapping relationships between architectural concepts and engineering components.
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.knowledge.graph")


class KnowledgeGraphBuilder:
    """
    Builds and queries the project Knowledge Graph.
    """

    def __init__(self) -> None:
        self.nodes: Dict[str, Dict[str, Any]] = {
            "Authentication": {"id": "Auth", "label": "Authentication Subsystem", "category": "Core"},
            "JWT": {"id": "JWT", "label": "JSON Web Tokens", "category": "Security"},
            "OAuth": {"id": "OAuth", "label": "OAuth2 / Google SSO", "category": "Security"},
            "RBAC": {"id": "RBAC", "label": "Role-Based Access Control", "category": "Security"},
            "React": {"id": "React", "label": "React Frontend Framework", "category": "Frontend"},
            "Hooks": {"id": "Hooks", "label": "React Custom Hooks", "category": "Frontend"},
            "StateManagement": {"id": "StateManagement", "label": "Redux / Zustand", "category": "Frontend"},
            "Database": {"id": "Database", "label": "PostgreSQL Database Engine", "category": "Backend"}
        }

        self.edges: List[Dict[str, str]] = [
            {"source": "Authentication", "target": "JWT", "relation": "IMPLEMENTS"},
            {"source": "Authentication", "target": "OAuth", "relation": "IMPLEMENTS"},
            {"source": "Authentication", "target": "RBAC", "relation": "ENFORCES"},
            {"source": "React", "target": "Hooks", "relation": "USES"},
            {"source": "React", "target": "StateManagement", "relation": "INTEGRATES"}
        ]

    def add_node(self, node_id: str, label: str, category: str = "General") -> Dict[str, Any]:
        node = {"id": node_id, "label": label, "category": category}
        self.nodes[node_id] = node
        return node

    def add_edge(self, source: str, target: str, relation: str = "DEPENDS_ON") -> Dict[str, str]:
        edge = {"source": source, "target": target, "relation": relation}
        self.edges.append(edge)
        return edge

    def get_graph(self) -> Dict[str, Any]:
        return self.get_full_graph()

    def get_full_graph(self) -> Dict[str, Any]:
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "nodes": list(self.nodes.values()),
            "edges": self.edges
        }

    def get_related_nodes(self, node_id: str) -> List[Dict[str, Any]]:
        related_ids = [e["target"] for e in self.edges if e["source"].lower() == node_id.lower()]
        related_ids += [e["source"] for e in self.edges if e["target"].lower() == node_id.lower()]
        return [n for k, n in self.nodes.items() if k.lower() in [r.lower() for r in related_ids]]


global_knowledge_graph_builder = KnowledgeGraphBuilder()
