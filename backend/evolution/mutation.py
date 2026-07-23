"""
AIForge Prompt & Agent Genome Mutation Engine
=============================================
Mutates agent system prompts and LLM genome configurations (temperature, top_p, context_size, model)
to produce higher-scoring agent variants.
"""

import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.evolution")


class AgentMutationEngine:
    """
    Mutates agent system prompts and hyperparameters.
    """

    def mutate_prompt(self, base_prompt: str, agent_role: str = "Planner") -> str:
        _logger.info(f"AgentMutationEngine: Mutating prompt for agent '{agent_role}'...")

        if "expert" in base_prompt.lower():
            return (
                f"You are an expert {agent_role} engineer focused on performance, "
                "accessibility, responsive UI, clean architecture, production-ready code, "
                "and high Lighthouse scores."
            )

        return base_prompt + " Enforce production-grade clean architecture, SOLID principles, and high test coverage."

    def mutate_genome(self, genome: Dict[str, Any]) -> Dict[str, Any]:
        mutated = dict(genome)
        mutated["temperature"] = round(max(0.1, min(0.7, genome.get("temperature", 0.3) - 0.05)), 2)
        mutated["version"] = f"v{int(genome.get('version_id', 1)) + 1}"
        return mutated


global_mutation_engine = AgentMutationEngine()
