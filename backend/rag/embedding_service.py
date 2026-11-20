"""
AIForge V2 — Centralized Embedding Service
Text-to-vector embeddings with batching and content-hash caching.

Vectors come from a local sentence-embedding model (backend/ml/local_models.py, default BAAI/bge-small-en-v1.5,
384 dimensions). Until this change no model was ever loaded here: every vector was the word-hash fallback below, so
"semantic" search matched hashed words, not meaning. The fallback is still used when the model is unavailable (switched
off, not downloaded); every vector is tagged with ``model_tag`` so vectors from different models are never compared.
"""
import os
import math
import hashlib
import logging
from typing import List, Dict, Optional

logger = logging.getLogger("aiforge.rag.embedding_service")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
HASH_TAG = "hash-v1"


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculates cosine similarity score between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 < 1e-6 or norm2 < 1e-6:
        return 0.0
    return dot / (norm1 * norm2)


def hash_embedding(text: str, dimension: int = 384) -> List[float]:
    """The fallback: a normalised vector of hashed words (not semantic; used only without the embedding model)."""
    vec = [0.0] * dimension
    for idx, word in enumerate(text.lower().split()):
        w_hash = hashlib.sha256(word.encode("utf-8")).digest()
        for b_idx, byte_val in enumerate(w_hash[:32]):
            vec[(b_idx * 12 + idx) % dimension] += (byte_val - 128) / 128.0
    norm = math.sqrt(sum(v * v for v in vec))
    return [v / norm for v in vec] if norm > 1e-6 else vec


class EmbeddingService:
    """Dense vectors from the local embedding model (or the labelled hash fallback), with batching and caching."""

    DIMENSION = 384
    MODEL_NAME = EMBEDDING_MODEL
    MODEL_VERSION = "v2.0"

    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self._cache: Dict[str, List[float]] = {}

    @property
    def model_tag(self) -> str:
        """What produces this process's vectors: the model id, or ``hash-v1`` for the fallback."""
        from backend.ml.local_models import get, model_id
        return (model_id("embeddings") or HASH_TAG) if get("embeddings") is not None else HASH_TAG

    def embed_document(self, text: str, content_hash: Optional[str] = None) -> List[float]:
        """Generates or retrieves vector embedding for a document chunk."""
        return self.get_embedding(text, content_hash=content_hash)

    def embed_query(self, query: str) -> List[float]:
        """Vector for a search query (the model's retrieval instruction is added for queries)."""
        return self.get_embedding(query, query=True)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embeddings for document chunks, computed in one model batch."""
        tag = self.model_tag
        keys = [self._key(t, tag, False) for t in texts]
        todo = [i for i, (t, k) in enumerate(zip(texts, keys)) if t and t.strip() and k not in self._cache]
        if todo:
            vectors = self._model_vectors([texts[i] for i in todo], query=False)
            for n, i in enumerate(todo):
                self._cache[keys[i]] = vectors[n] if vectors else hash_embedding(texts[i], self.DIMENSION)
        return [self._cache.get(k) or [0.0] * self.DIMENSION for k in keys]

    def get_embedding(self, text: str, content_hash: Optional[str] = None, query: bool = False) -> List[float]:
        """Generates or retrieves cached vector embedding for text."""
        if not text or not text.strip():
            return [0.0] * self.DIMENSION
        tag = self.model_tag
        key = self._key(text, tag, query, content_hash)
        if key not in self._cache:
            vectors = self._model_vectors([text], query=query)
            self._cache[key] = vectors[0] if vectors else hash_embedding(text, self.DIMENSION)
        return self._cache[key]

    def get_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        return self.embed_batch(texts)

    def clear_cache(self) -> None:
        """Clears in-memory embedding cache."""
        self._cache.clear()

    @staticmethod
    def _key(text: str, tag: str, query: bool, content_hash: Optional[str] = None) -> str:
        h = content_hash or hashlib.sha256((text or "").encode("utf-8")).hexdigest()
        return f"{tag}|{'q' if query else 'd'}|{h}"

    @staticmethod
    def _model_vectors(texts: List[str], query: bool) -> Optional[List[List[float]]]:
        from backend.ml.local_models import embed
        try:
            return embed(texts, query=query)
        except Exception as e:  # noqa: BLE001 - the fallback keeps retrieval working
            logger.warning(f"Embedding model error ({e}); using the hash fallback")
            return None


# Global Singleton
global_embedding_service = EmbeddingService()
