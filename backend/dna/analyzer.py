"""
AIForge Day 15 — Main Orchestrator DNA Analyzer
================================================
Combines multi-language code parsing, dependency linking, and graph repository storage.
"""

import logging
from typing import Dict, Any, List

from backend.dna.models import EngineeringDNAGraph, GraphNode, GraphEdge
from backend.dna.parser import global_code_parser
from backend.dna.dependency import global_dependency_extractor
from backend.dna.repository import global_graph_repository

_logger = logging.getLogger("aiforge.dna.analyzer")


class DNAAnalyzer:
    """
    Orchestrates static analysis and builds the Engineering DNA graph.
    """

    def analyze_project(
        self,
        project_id: str,
        files_map: Dict[str, str],
        requirements: List[Dict[str, Any]] = None
    ) -> EngineeringDNAGraph:
        if requirements is None:
            requirements = [
                {"id": "req_1", "text": "Users must be able to authenticate and log in."},
                {"id": "req_2", "text": "Users can view product catalog and search products."},
                {"id": "req_3", "text": "Users can create orders and make payments."},
            ]

        all_nodes: List[GraphNode] = []
        all_edges: List[GraphEdge] = []

        for path, content in files_map.items():
            nodes, edges = global_code_parser.parse_file(path, content)
            all_nodes.extend(nodes)
            all_edges.extend(edges)

        # Link dependencies and requirements
        final_nodes, final_edges = global_dependency_extractor.link_graph_dependencies(
            all_nodes, all_edges, requirements
        )

        # Deduplicate nodes by id
        unique_nodes_map = {n.id: n for n in final_nodes}
        unique_nodes = list(unique_nodes_map.values())

        graph = EngineeringDNAGraph(
            project_id=project_id,
            nodes=unique_nodes,
            edges=final_edges
        )

        return global_graph_repository.save_graph(graph)


global_dna_analyzer = DNAAnalyzer()
