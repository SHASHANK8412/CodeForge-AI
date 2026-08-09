"""
AIForge Day 15 — Dependency Extractor & Linker
==============================================
Links components, API endpoints, backend services, database tables, requirements, and tests into a unified graph.
"""

import logging
from typing import Dict, Any, List, Tuple

from backend.dna.models import GraphNode, GraphEdge, NodeKind, RelationType

_logger = logging.getLogger("aiforge.dna.dependency")


class DependencyExtractor:
    """
    Infers missing relations and links requirements to software components and tests.
    """

    def link_graph_dependencies(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        requirements: List[Dict[str, Any]]
    ) -> Tuple[List[GraphNode], List[GraphEdge]]:

        node_map = {n.id: n for n in nodes}
        new_edges: List[GraphEdge] = list(edges)

        # 1. Link APIs to Database Models / Tables
        api_nodes = [n for n in nodes if n.kind == NodeKind.API]
        db_nodes = [n for n in nodes if n.kind in (NodeKind.DATABASE_MODEL, NodeKind.DATABASE_TABLE)]

        for api in api_nodes:
            for db in db_nodes:
                # If API name and DB name share common domain word (e.g. order, user, auth)
                api_words = set(api.label.lower().split("_"))
                db_words = set(db.label.lower().split("_"))
                if api_words.intersection(db_words):
                    new_edges.append(
                        GraphEdge(
                            source=api.id,
                            target=db.id,
                            relation=RelationType.STORES_IN
                        )
                    )

        # 2. Link Requirements to Features and Components
        for req in requirements:
            req_id = f"req:{req.get('id', req.get('text', '')[:12])}"
            req_label = req.get('text', 'Requirement')
            req_node = GraphNode(
                id=req_id,
                label=req_label,
                kind=NodeKind.REQUIREMENT,
                security_critical="auth" in req_label.lower() or "payment" in req_label.lower()
            )
            nodes.append(req_node)

            # Link to matching component/API
            req_lower = req_label.lower()
            for n in nodes:
                if n.kind in (NodeKind.COMPONENT, NodeKind.API, NodeKind.FEATURE):
                    if any(w in req_lower for w in n.label.lower().split("_")):
                        new_edges.append(
                            GraphEdge(
                                source=req_node.id,
                                target=n.id,
                                relation=RelationType.REQUIRES
                            )
                        )

        # 3. Link Tests to Functions / Classes
        test_nodes = [n for n in nodes if n.kind == NodeKind.TEST]
        impl_nodes = [n for n in nodes if n.kind in (NodeKind.FUNCTION, NodeKind.CLASS, NodeKind.COMPONENT)]

        for t in test_nodes:
            clean_t_name = t.label.lower().replace("test_", "").replace("_test", "")
            for impl in impl_nodes:
                if clean_t_name in impl.label.lower():
                    new_edges.append(
                        GraphEdge(
                            source=t.id,
                            target=impl.id,
                            relation=RelationType.TESTS
                        )
                    )

        return nodes, new_edges


global_dependency_extractor = DependencyExtractor()
