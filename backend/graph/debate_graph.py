import json
import logging
from pathlib import Path
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.graph")

class DebateGraphVisualizer:
    """
    Exports a visual debate graph representation (JSON) mapping nodes, consensus, and votes.
    """

    def __init__(self, output_path: str = None) -> None:
        if output_path is None:
            output_path = str(Path(__file__).resolve().parent.parent / "debate_graph.json")
        self.output_path = Path(output_path)

    def generate_and_save_graph(
        self,
        participants: List[str],
        votes: Dict[str, str],
        consensus: str,
        arguments: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Builds the nodes and links edge matrix mapping debate execution.
        """
        # Node Definitions
        nodes = [
            {"id": "planner", "label": "Planner"},
            {"id": "architect", "label": "Architect"},
            {"id": "debate_engine", "label": "Debate Engine"},
            {"id": "consensus", "label": "Consensus"}
        ]
        
        # Add dynamic agent participant nodes
        for part in participants:
            nodes.append({"id": part, "label": part.capitalize()})

        # Edge Definitions (Debate flows)
        edges = [
            {"source": "planner", "target": "architect"},
            {"source": "architect", "target": "debate_engine"}
        ]
        
        for part in participants:
            edges.append({"source": "debate_engine", "target": part})
            edges.append({"source": part, "target": "consensus"})

        graph_data = {
            "nodes": nodes,
            "edges": edges,
            "votes": votes,
            "consensus_choice": consensus,
            "arguments": arguments or {
                "REST": "High standard API throughput",
                "JWT": "Secure token stateless verification"
            }
        }

        try:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.output_path, "w", encoding="utf-8") as f:
                json.dump(graph_data, f, indent=2)
            _logger.info(f"Successfully exported visual debate graph: {self.output_path.name}")
        except Exception as e:
            _logger.error(f"Failed to write visual debate_graph.json: {str(e)}")

        return graph_data
