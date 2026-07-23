"""
AIForge Vector Memory Store
===========================
Persistent vector database storing project embeddings, code snippets, and architectural patterns.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.learning.embeddings import global_embedding_engine

_logger = logging.getLogger("aiforge.memory")


class VectorMemoryStore:
    """
    Vector memory store index.
    """

    def __init__(self, store_path: Optional[str] = None) -> None:
        if store_path is None:
            mem_dir = Path(__file__).resolve().parent
            mem_dir.mkdir(parents=True, exist_ok=True)
            store_path = str(mem_dir / "vector_store.json")
        self.store_file = Path(store_path)
        self._init_store()

    def _init_store(self) -> None:
        if not self.store_file.exists():
            default_vectors = [
                {
                    "id": "proj_restaurant",
                    "text": "Restaurant Food Delivery App with FastAPI, React, and MongoDB",
                    "vector": global_embedding_engine.generate_embedding("Restaurant Food Delivery App with FastAPI, React, and MongoDB"),
                    "metadata": {"project_name": "Restaurant App", "stack": ["FastAPI", "React", "MongoDB"]}
                }
            ]
            self._save_vectors(default_vectors)

    def _load_vectors(self) -> List[Dict[str, Any]]:
        try:
            with open(self.store_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_vectors(self, vectors: List[Dict[str, Any]]) -> None:
        try:
            with open(self.store_file, "w", encoding="utf-8") as f:
                json.dump(vectors, f, indent=2)
        except Exception as e:
            _logger.error(f"Failed to save vector_store.json: {e}")

    def add_vector(self, doc_id: str, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        vectors = self._load_vectors()
        vec = global_embedding_engine.generate_embedding(text)
        entry = {
            "id": doc_id,
            "text": text,
            "vector": vec,
            "metadata": metadata
        }
        vectors.append(entry)
        self._save_vectors(vectors)
        return entry

    def search_similar(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query_vec = global_embedding_engine.generate_embedding(query_text)
        vectors = self._load_vectors()
        results = []
        for item in vectors:
            sim = global_embedding_engine.cosine_similarity(query_vec, item["vector"])
            results.append({
                "id": item["id"],
                "similarity_score": sim,
                "text": item["text"],
                "metadata": item["metadata"]
            })

        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]


global_vector_memory = VectorMemoryStore()
VectorMemory = VectorMemoryStore
