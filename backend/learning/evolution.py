"""
AIForge Day 89 Evolution Engine & Knowledge Graph
=================================================
Evolves system memory, architecture templates, prompt library, and knowledge base after each completed project.
Builds an interactive Knowledge Graph linking technologies, patterns, frameworks, and projects.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.learning")


class EvolutionEngine:
    """
    Evolves AIForge memory and knowledge graph across project generations.
    """

    def __init__(self, graph_path: Optional[str] = None) -> None:
        if graph_path is None:
            g_dir = Path(__file__).resolve().parent
            g_dir.mkdir(parents=True, exist_ok=True)
            graph_path = str(g_dir / "knowledge_graph.json")
        self.graph_file = Path(graph_path)
        self._init_graph()

    def _init_graph(self) -> None:
        if not self.graph_file.exists():
            default_graph = {
                "nodes": [
                    {"id": "JWT", "type": "Security"},
                    {"id": "Authentication", "type": "Pattern"},
                    {"id": "FastAPI", "type": "Backend Framework"},
                    {"id": "React", "type": "Frontend Framework"},
                    {"id": "MongoDB", "type": "Database"},
                    {"id": "AI Resume Analyzer", "type": "Project"},
                    {"id": "Docker Container", "type": "Deployment"}
                ],
                "edges": [
                    {"source": "JWT", "target": "Authentication", "relation": "provides"},
                    {"source": "Authentication", "target": "FastAPI", "relation": "implemented_in"},
                    {"source": "FastAPI", "target": "React", "relation": "connects_with"},
                    {"source": "React", "target": "MongoDB", "relation": "persists_to"},
                    {"source": "FastAPI", "target": "AI Resume Analyzer", "relation": "powers"},
                    {"source": "AI Resume Analyzer", "target": "Docker Container", "relation": "deployed_via"}
                ]
            }
            self._save_graph(default_graph)

    def _load_graph(self) -> Dict[str, Any]:
        try:
            with open(self.graph_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"nodes": [], "edges": []}

    def _save_graph(self, graph: Dict[str, Any]) -> None:
        try:
            with open(self.graph_file, "w", encoding="utf-8") as f:
                json.dump(graph, f, indent=2)
        except Exception as e:
            _logger.error(f"Failed to save knowledge_graph.json: {e}")

    def evolve_system(self, project_name: str, tech_stack: List[str]) -> Dict[str, Any]:
        _logger.info(f"EvolutionEngine: Evolving AI system memory for project '{project_name}'...")
        graph = self._load_graph()

        # Add project node
        if not any(n["id"] == project_name for n in graph["nodes"]):
            graph["nodes"].append({"id": project_name, "type": "Project"})

        for tech in tech_stack:
            if not any(n["id"] == tech for n in graph["nodes"]):
                graph["nodes"].append({"id": tech, "type": "Technology"})
            graph["edges"].append({"source": tech, "target": project_name, "relation": "used_in"})

        self._save_graph(graph)

        return {
            "status": "success",
            "project_name": project_name,
            "total_knowledge_nodes": len(graph["nodes"]),
            "total_knowledge_edges": len(graph["edges"]),
            "evolution_message": f"Updated AI memory & Knowledge Graph with {len(tech_stack)} tech nodes."
        }

    def get_knowledge_graph(self) -> Dict[str, Any]:
        return self._load_graph()


global_evolution_engine = EvolutionEngine()
