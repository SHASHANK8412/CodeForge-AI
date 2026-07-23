"""
AIForge Semantic Similarity Search Engine
==========================================
Searches stored project memory using vector embeddings to retrieve similar past projects.
"""

import logging
from typing import Dict, Any, List
from backend.memory.vector_memory import global_vector_memory

_logger = logging.getLogger("aiforge.learning")


class SemanticSimilarityEngine:
    """
    Retrieves similar projects and reusable artifacts using vector embeddings.
    """

    def find_similar_projects(self, query_prompt: str, top_k: int = 3) -> List[Dict[str, Any]]:
        _logger.info(f"SemanticSimilarityEngine: Searching for projects similar to '{query_prompt}'...")
        results = global_vector_memory.search_similar(query_prompt, top_k=top_k)

        # Format output
        formatted = []
        for res in results:
            formatted.append({
                "project_id": res["id"],
                "similarity_percentage": f"{round(res['similarity_score'] * 100, 1)}%",
                "similarity_score_numeric": res["similarity_score"],
                "project_description": res["text"],
                "metadata": res["metadata"]
            })

        return formatted


global_similarity_engine = SemanticSimilarityEngine()
SimilaritySearchEngine = SemanticSimilarityEngine
