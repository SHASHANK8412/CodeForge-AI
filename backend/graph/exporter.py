"""
AIForge Knowledge Graph Exporter
================================
Exports Knowledge Graph to Mermaid Markdown docs, JSON schemas, or GraphML files.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import networkx as nx
from backend.graph.visualizer import GraphVisualizer
from backend.memory.graph_memory import GraphMemory

_logger = logging.getLogger("aiforge.graph")


class GraphExporter:
    """
    Exports knowledge graph formats to files.
    """

    def __init__(self, G: Optional[nx.DiGraph] = None) -> None:
        if G is None:
            memory = GraphMemory()
            G = memory.load_graph()
        self.G = G
        self.visualizer = GraphVisualizer(self.G)

    def export_mermaid_markdown(self, output_path: str) -> str:
        mermaid_code = self.visualizer.generate_mermaid_diagram(max_edges=40)
        content = f"# AIForge Codebase Dependency Graph\n\n```mermaid\n{mermaid_code}\n```\n"
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        _logger.info(f"GraphExporter: Exported Mermaid diagram to '{output_path}'")
        return content
