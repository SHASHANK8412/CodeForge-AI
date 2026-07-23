"""
AIForge Vector Embeddings Generator
====================================
Generates lightweight numerical feature embeddings for project descriptions,
architectures, and module summaries to power semantic similarity matching in ChromaDB.
"""

import math
import logging
from typing import List, Dict, Any

_logger = logging.getLogger("aiforge.learning")


class EmbeddingsGenerator:
    """
    Generates feature vector embeddings for project prompts and summaries.
    """

    def generate_embedding(self, text: str, vector_dim: int = 64) -> List[float]:
        """
        Generates deterministic 64-dimensional feature vector for input text.
        """
        words = text.lower().split()
        vec = [0.0] * vector_dim
        for idx, word in enumerate(words):
            word_hash = hash(word) % vector_dim
            vec[word_hash] += (1.0 / (idx + 1.0))

        # Normalize vector to unit length
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]

        return vec

    def compute_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Computes cosine similarity between two feature vectors.
        """
        if len(vec1) != len(vec2) or not vec1 or not vec2:
            return 0.0

        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return max(0.0, min(1.0, dot / (norm1 * norm2)))
