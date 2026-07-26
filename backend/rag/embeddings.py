import math
import hashlib
import logging
from typing import List

logger = logging.getLogger("aiforge.rag.embeddings")


class EmbeddingGenerator:
    """
    EmbeddingGenerator converts text strings into dense vector representations.
    Supports SentenceTransformers if available, or a fast, normalized 384-dimensional
    dense vector generator fallback.
    """

    DIMENSION = 384

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._st_model = None

        try:
            from sentence_transformers import SentenceTransformer
            self._st_model = SentenceTransformer(model_name)
            logger.info(f"Initialized SentenceTransformer embedding model: '{model_name}'")
        except Exception as e:
            logger.info(f"SentenceTransformer not loaded ({e}); using dense hash embedding generator.")

    def generate_embedding(self, text: str) -> List[float]:
        """Generates a normalized 384-dimensional vector embedding for the input text."""
        if not text or not text.strip():
            return [0.0] * self.DIMENSION

        if self._st_model is not None:
            try:
                vector = self._st_model.encode(text).tolist()
                return vector
            except Exception as e:
                logger.warning(f"Error during SentenceTransformer encoding: {e}")

        # Fallback dense normalized vector generator
        vector = [0.0] * self.DIMENSION
        words = text.lower().split()
        for idx, word in enumerate(words):
            # Compute hash digest
            h = hashlib.sha256(word.encode("utf-8")).digest()
            for b_idx, byte_val in enumerate(h[:32]):
                target_idx = (b_idx * 12 + idx) % self.DIMENSION
                vector[target_idx] += (byte_val - 128) / 128.0

        # L2 Normalize
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 1e-6:
            vector = [v / norm for v in vector]

        return vector

    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a batch of text strings."""
        return [self.generate_embedding(t) for t in texts]
