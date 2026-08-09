"""
AIForge Memory Retriever Service (Day 44)
=========================================
Searches long-term memory for relevant past projects, proven components, and error resolution pairs to inject context into new generation pipelines.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.services.memory_retriever")


class MemoryRetriever:
    """
    Retrieves similar project memories, solutions, and patterns for new prompts.
    """

    def __init__(self, memory_dir: Optional[Path] = None):
        _root = Path(__file__).resolve().parent.parent.parent
        self.memory_dir = memory_dir or (_root / "backend" / "memory")
        self.projects_dir = self.memory_dir / "projects"
        self.patterns_dir = self.memory_dir / "patterns"
        self.solutions_dir = self.memory_dir / "solutions"

    def search_similar_projects(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Searches project memory files and scores similarity against the query prompt.
        """
        results = []
        query_words = set(query.lower().split())

        if self.projects_dir.exists():
            for p_file in self.projects_dir.glob("*.json"):
                try:
                    data = json.loads(p_file.read_text(encoding="utf-8"))
                    prompt_text = data.get("prompt", "").lower()
                    tags = set(data.get("tags", []))

                    # Calculate keyword overlap score
                    matches = len(query_words.intersection(set(prompt_text.split()).union(tags)))
                    score = min(1.0, (matches + 1) / max(1, len(query_words)))

                    results.append({
                        "project_id": data.get("project_id"),
                        "prompt": data.get("prompt"),
                        "similarity_score": round(score, 2),
                        "quality_score": data.get("quality_score", 95.0),
                        "framework": data.get("framework", "FullStack"),
                        "knowledge": data.get("knowledge", {})
                    })
                except Exception as e:
                    _logger.error(f"MemoryRetriever: Error reading project file {p_file}: {e}")

        # Sort by similarity and quality
        results.sort(key=lambda x: (x["similarity_score"], x["quality_score"]), reverse=True)
        return results[:top_k]

    def retrieve_context_for_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Retrieves top-5 similar project memories and formats context snippet for injection into generation agents.
        """
        similar_projects = self.search_similar_projects(prompt, top_k=5)

        reusable_components = []
        proven_solutions = []

        for proj in similar_projects:
            know = proj.get("knowledge", {})
            reusable_components.extend(know.get("ui_components", []))
            proven_solutions.extend(know.get("error_resolution_pairs", []))

        context_prompt = (
            f"=== Long-Term AI Memory Context ===\n"
            f"Found {len(similar_projects)} similar past projects in long-term memory.\n"
            f"Proven Patterns: {len(reusable_components)} components, {len(proven_solutions)} solutions.\n"
        )

        return {
            "query": prompt,
            "similar_projects_count": len(similar_projects),
            "similar_projects": similar_projects,
            "reusable_components": reusable_components[:5],
            "proven_solutions": proven_solutions[:5],
            "context_prompt_snippet": context_prompt
        }


global_memory_retriever = MemoryRetriever()
