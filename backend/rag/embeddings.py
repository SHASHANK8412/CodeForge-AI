import logging
from typing import List

logger = logging.getLogger("aiforge.rag.embeddings")


class EmbeddingGenerator:
    """
    Text to dense vectors for the knowledge base and the legacy retriever. Delegates to the shared EmbeddingService
    (backend/rag/embedding_service.py): the local embedding model, or its labelled hash fallback. (This class used to
    set its model to None and always return hashed-word vectors.)
    """

    DIMENSION = 384

    def __init__(self, model_name: str = ""):
        from backend.rag.embedding_service import global_embedding_service
        self._service = global_embedding_service
        self.model_name = model_name or global_embedding_service.model_name

    @property
    def model_tag(self) -> str:
        return self._service.model_tag

    def generate_embedding(self, text: str) -> List[float]:
        """A normalised 384-dimensional vector for the input text."""
        return self._service.get_embedding(text)

    def generate_query_embedding(self, query: str) -> List[float]:
        return self._service.embed_query(query)

    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Embeddings for a batch of text strings."""
        return self._service.embed_batch(texts)
