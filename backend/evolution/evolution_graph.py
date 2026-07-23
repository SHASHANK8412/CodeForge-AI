"""
AIForge Evolution Graph & AI Genome Store
=========================================
Stores AI Genomes for specialized agents:
Prompt, Configuration, Model, Temperature, Top_p, Context Size, Memory Usage, Success Rate, Average Score.
Tracks agent evolution lineage across versions (V1 -> V2 -> V3).
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.evolution")


class EvolutionGraphStore:
    """
    Persistent store for agent genome lineages and evolution graphs.
    """

    def __init__(self, store_path: Optional[str] = None) -> None:
        if store_path is None:
            e_dir = Path(__file__).resolve().parent
            e_dir.mkdir(parents=True, exist_ok=True)
            store_path = str(e_dir / "evolution_genomes.json")
        self.store_file = Path(store_path)
        self._init_store()

    def _init_store(self) -> None:
        if not self.store_file.exists():
            default_genomes = {
                "Planner": {
                    "agent_role": "Planner",
                    "version": "v1.0",
                    "version_id": 1,
                    "prompt": "You are an expert Planner Agent.",
                    "model": "qwen2.5-coder:latest",
                    "temperature": 0.2,
                    "top_p": 0.9,
                    "context_size": 16384,
                    "memory_usage_mb": 42.0,
                    "success_rate_pct": 98.0,
                    "average_score": 93.5
                },
                "Reviewer": {
                    "agent_role": "Reviewer",
                    "version": "v1.0",
                    "version_id": 1,
                    "prompt": "You are an expert Reviewer Agent.",
                    "model": "qwen2.5-coder:latest",
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "context_size": 16384,
                    "memory_usage_mb": 38.0,
                    "success_rate_pct": 99.0,
                    "average_score": 95.0
                }
            }
            self._save_genomes(default_genomes)

    def _load_genomes(self) -> Dict[str, Any]:
        try:
            with open(self.store_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_genomes(self, data: Dict[str, Any]) -> None:
        try:
            with open(self.store_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            _logger.error(f"Failed to save evolution_genomes.json: {e}")

    def get_agent_genome(self, agent_role: str) -> Dict[str, Any]:
        genomes = self._load_genomes()
        return genomes.get(agent_role, {
            "agent_role": agent_role,
            "version": "v1.0",
            "version_id": 1,
            "prompt": f"You are an expert {agent_role} Agent.",
            "temperature": 0.2,
            "average_score": 92.0
        })

    def update_agent_genome(self, agent_role: str, updated_genome: Dict[str, Any]) -> Dict[str, Any]:
        genomes = self._load_genomes()
        genomes[agent_role] = updated_genome
        self._save_genomes(genomes)
        _logger.info(f"EvolutionGraphStore: Updated genome for agent '{agent_role}' (Version={updated_genome.get('version')})")
        return updated_genome


global_evolution_graph_store = EvolutionGraphStore()
