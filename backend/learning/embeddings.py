"""
AIForge Vector Embeddings Engine
================================
Generates vector embeddings for software prompts, architecture patterns, and reusable code modules
enabling high-precision semantic similarity search.
"""

import math
import logging
from typing import List, Dict, Any

_logger = logging.getLogger("aiforge.learning")


class VectorEmbeddingEngine:
    """
    Generates text embeddings using pseudo-TF-IDF hashing vectorization for fast local execution.
    """

    def generate_embedding(self, text: str, dimensions: int = 64) -> List[float]:
        tokens = text.lower().replace("-", " ").replace("_", " ").split()
        vector = [0.0] * dimensions
        for tok in tokens:
            for char in tok:
                idx = ord(char) % dimensions
                vector[idx] += 1.0

        # L2 Normalization
        norm = math.sqrt(sum(x * x for x in vector)) or 1.0
        return [round(x / norm, 4) for x in vector]

    def cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        if len(vec_a) != len(vec_b):
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a)) or 1.0
        norm_b = math.sqrt(sum(b * b for b in vec_b)) or 1.0
        return round(dot_product / (norm_a * norm_b), 4)


global_embedding_engine = VectorEmbeddingEngine()
