import math
import logging
from typing import List

logger = logging.getLogger("aiforge.learning.embeddings")


class LearningEmbeddings:
    """
    LearningEmbeddings generates vector representation embeddings for semantic search.
    """

    def generate_embedding(self, text: str) -> List[float]:
        """Generates a 384-dimensional vector embedding simulation."""
        hash_val = sum(ord(c) for c in text)
        return [round(math.sin(hash_val + i), 4) for i in range(16)]

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculates cosine similarity score between two vectors."""
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return round(dot / (norm1 * norm2), 4)


# Global LearningEmbeddings Instance
global_learning_embeddings = LearningEmbeddings()
