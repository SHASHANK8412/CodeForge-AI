"""
AIForge Knowledge Graph Visualizer
===================================
Converts NetworkX Knowledge Graph into D3.js JSON schemas and Mermaid Markdown diagrams.
"""

import logging
from typing import Dict, Any, List, Optional
import networkx as nx
from backend.memory.graph_memory import GraphMemory

_logger = logging.getLogger("aiforge.graph")


class GraphVisualizer:
    """
    Formats NetworkX graph into D3-compatible nodes/links JSON and Mermaid diagrams.
    """

    def __init__(self, G: Optional[nx.DiGraph] = None) -> None:
        if G is None:
            memory = GraphMemory()
            G = memory.load_graph()
        self.G = G

    def get_d3_schema(self, max_nodes: int = 100) -> Dict[str, Any]:
        """
        Returns JSON schema formatted for D3 force graphs.
        """
        nodes = []
        links = []

        sub_nodes = list(self.G.nodes())[:max_nodes]
        sub_G = self.G.subgraph(sub_nodes)

        for n in sub_G.nodes():
            data = sub_G.nodes[n]
            n_type = data.get("node_type", "file")
            color = "#6366f1" # default blue
            if n_type == "api":
                color = "#10b981" # green
            elif n_type == "database_model":
                color = "#f59e0b" # amber
            elif n_type == "class":
                color = "#ec4899" # pink

            nodes.append({
                "id": str(n),
                "label": str(n),
                "type": n_type,
                "color": color
            })

        for u, v, data in sub_G.edges(data=True):
            links.append({
                "source": str(u),
                "target": str(v),
                "relation": data.get("relation", "DEPENDS")
            })

        return {"nodes": nodes, "links": links}

    def generate_mermaid_diagram(self, max_edges: int = 25) -> str:
        """
        Generates Mermaid flow graph markdown string.
        """
        lines = ["graph TD;"]
        count = 0
        for u, v, data in self.G.edges(data=True):
            if count >= max_edges:
                break
            u_clean = str(u).replace("/", "_").replace(".", "_").replace(" ", "_").replace(":", "_")
            v_clean = str(v).replace("/", "_").replace(".", "_").replace(" ", "_").replace(":", "_")
            rel = data.get("relation", "DEPENDS")
            lines.append(f"    {u_clean}[\"{u}\"] -->|{rel}| {v_clean}[\"{v}\"]")
            count += 1

        return "\n".join(lines)
