"""
AIForge Graph Memory Store
==========================
Persists and retrieves the Project Knowledge Graph in backend/memory/project_graph.json.
Provides helper methods for NetworkX graph serialization and deserialization.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import networkx as nx

_logger = logging.getLogger("aiforge.graph")


class GraphMemory:
    """
    Manages persistence of NetworkX Project Knowledge Graph.
    """

    def __init__(self, memory_dir: Optional[str] = None) -> None:
        if memory_dir is None:
            memory_dir = str(Path(__file__).resolve().parents[0])
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.memory_dir / "project_graph.json"

    def save_graph(self, G: nx.DiGraph, summary: Optional[Dict[str, Any]] = None) -> str:
        """
        Serializes NetworkX DiGraph into JSON structure.
        """
        data = nx.node_link_data(G)
        data["summary"] = summary or {
            "total_nodes": G.number_of_nodes(),
            "total_edges": G.number_of_edges()
        }

        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            _logger.info(f"GraphMemory: Saved graph to {self.file_path} ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)")
            return str(self.file_path)
        except Exception as e:
            _logger.error(f"Failed to save project_graph.json: {e}")
            return ""

    def load_graph(self) -> nx.DiGraph:
        """
        Deserializes NetworkX DiGraph from project_graph.json.
        """
        if not self.file_path.exists() or self.file_path.stat().st_size == 0:
            _logger.warning("project_graph.json does not exist. Returning empty DiGraph.")
            return nx.DiGraph()

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Remove summary metadata before networkx conversion if present
            data_copy = {k: v for k, v in data.items() if k != "summary"}
            G = nx.node_link_graph(data_copy, directed=True)
            _logger.info(f"GraphMemory: Loaded graph with {G.number_of_nodes()} nodes, {G.number_of_edges()} edges.")
            return G
        except Exception as e:
            _logger.error(f"Failed to load project_graph.json: {e}")
            return nx.DiGraph()

    def get_summary(self) -> Dict[str, Any]:
        if not self.file_path.exists():
            return {"status": "empty", "total_nodes": 0, "total_edges": 0}

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("summary", {
                "total_nodes": len(data.get("nodes", [])),
                "total_edges": len(data.get("links", []))
            })
        except Exception:
            return {"status": "error"}
