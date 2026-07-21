import json
import logging
from pathlib import Path
from typing import Dict, Any
from backend.knowledge.graph.knowledge_graph import KnowledgeGraph

_logger = logging.getLogger("aiforge.knowledge")

class GraphVisualizer:
    """
    Exports Knowledge Graph elements to JSON for rendering inside frontend interfaces.
    """

    def __init__(self, graph: KnowledgeGraph, output_path: str = None) -> None:
        self.graph = graph
        if output_path is None:
            output_path = str(Path(__file__).resolve().parent.parent / "knowledge_graph.json")
        self.output_path = Path(output_path)

    def export_graph_json(self) -> Dict[str, Any]:
        """
        Gathers database elements and writes knowledge_graph.json.
        """
        nodes = self.graph.get_all_nodes()
        edges = self.graph.get_all_edges()

        # Format elements
        graph_data = {
            "nodes": [{"id": n["name"], "label": n["name"].capitalize(), "group": n["category"]} for n in nodes],
            "edges": [{"from": e["source"], "to": e["target"], "label": e["relation"]} for e in edges]
        }

        try:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.output_path, "w", encoding="utf-8") as f:
                json.dump(graph_data, f, indent=2)
            _logger.info(f"Successfully exported SRE Knowledge Graph JSON: {self.output_path.name}")
        except Exception as e:
            _logger.error(f"Failed to export knowledge_graph.json: {str(e)}")

        return graph_data
