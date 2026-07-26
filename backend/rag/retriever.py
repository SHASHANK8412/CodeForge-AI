import logging
from typing import Dict, Any, List
from backend.rag.embeddings import EmbeddingGenerator
from backend.rag.vector_store import VectorStore

logger = logging.getLogger("aiforge.rag.retriever")


class SemanticRetriever:
    """
    SemanticRetriever converts natural language search queries into embedding vectors,
    executes similarity searches against the VectorStore, and returns formatted context blocks.
    """

    def __init__(self, vector_store: VectorStore = None, embedding_generator: EmbeddingGenerator = None):
        self.embedding_generator = embedding_generator or EmbeddingGenerator()
        self.vector_store = vector_store or VectorStore()

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieves top_k semantic search result dicts for the given user query."""
        if not query or not query.strip():
            return []

        query_vector = self.embedding_generator.generate_embedding(query)
        results = self.vector_store.search(query_vector, top_k=top_k)
        logger.info(f"Retrieved {len(results)} chunk(s) for query: '{query[:30]}...'")
        return results

    def retrieve_context_string(self, query: str, top_k: int = 5) -> str:
        """Formats retrieved chunks into a clean, markdown-formatted context string for LLM injection."""
        results = self.retrieve(query, top_k=top_k)
        if not results:
            return "No relevant documentation or guidelines retrieved."

        lines = ["### Retrieved Knowledge & Documentation"]
        for idx, res in enumerate(results, 1):
            source = res.get("source", "doc")
            text = res.get("text", "").strip()
            score = res.get("score", 0.0)
            lines.append(f"**[{idx}] Source: {source} (Relevance Score: {score})**\n{text}\n")

        return "\n".join(lines)
