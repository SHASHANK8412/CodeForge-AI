import logging
from typing import Dict, Any, List

from backend.learning.knowledge_base import global_knowledge_base
from backend.learning.embeddings import global_learning_embeddings

logger = logging.getLogger("aiforge.learning.retriever")


class KnowledgeRetriever:
    """
    KnowledgeRetriever performs semantic vector search over the KnowledgeBase,
    returning top matching architectural patterns and solutions.
    """

    def search_knowledge(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        query_vec = global_learning_embeddings.generate_embedding(query)
        entries = global_knowledge_base.list_knowledge()
        results = []

        for item in entries:
            text = f"{item['name']} {item['description']} {' '.join(item.get('tags', []))}"
            item_vec = global_learning_embeddings.generate_embedding(text)
            sim_score = global_learning_embeddings.cosine_similarity(query_vec, item_vec)
            combined_score = round((sim_score * 0.5) + (item.get("confidence_score", 9.0) / 20.0), 3)

            results.append({
                "knowledge_item": item,
                "similarity_score": sim_score,
                "confidence_score": item.get("confidence_score", 9.0),
                "combined_score": combined_score
            })

        results.sort(key=lambda r: r["combined_score"], reverse=True)
        logger.info(f"KnowledgeRetriever found {len(results)} matches for query '{query[:30]}'")
        return results[:top_k]


# Global KnowledgeRetriever Instance
global_knowledge_retriever = KnowledgeRetriever()
