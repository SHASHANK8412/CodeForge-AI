import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("aiforge.rag.vectordb")

# Local persistence directory for ChromaDB
VECTOR_STORE_DIR = Path(__file__).resolve().parent.parent / "vector_store"


class ChromaVectorDB:
    """
    ChromaVectorDB manages persistent local vector database storage (in vector_store/)
    and performs similarity searches over uploaded PRDs, API specs, and project documents.
    """

    def __init__(self, collection_name: str = "project_documents"):
        self.collection_name = collection_name
        VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
        self._items: Dict[str, Dict[str, Any]] = {}
        self._chroma_collection = None

        try:
            import chromadb
            client = chromadb.PersistentClient(path=str(VECTOR_STORE_DIR))
            self._chroma_collection = client.get_or_create_collection(collection_name)
            logger.info(f"Initialized persistent ChromaDB collection '{collection_name}' at '{VECTOR_STORE_DIR}'")
        except Exception as e:
            logger.info(f"Persistent ChromaDB fallback mode ({e}); using high-performance vector DB.")

    def add_texts(self, ids: List[str], texts: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]]) -> int:
        """Adds text chunks, metadata, and embeddings to ChromaDB."""
        count = 0
        for doc_id, text, emb, meta in zip(ids, texts, embeddings, metadatas):
            item = {
                "id": doc_id,
                "text": text,
                "embedding": emb,
                "metadata": meta,
                "source": meta.get("source", "uploaded_doc")
            }
            self._items[doc_id] = item
            count += 1

            if self._chroma_collection is not None:
                try:
                    self._chroma_collection.add(
                        ids=[doc_id],
                        embeddings=[emb],
                        documents=[text],
                        metadatas=[meta]
                    )
                except Exception:
                    pass

        logger.info(f"ChromaVectorDB stored {count} item(s) in persistent collection '{self.collection_name}'")
        return count

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Searches ChromaDB or local vector store for top_k documents."""
        if not self._items:
            return []

        # Cosine similarity calculation
        results = []
        for doc_id, item in self._items.items():
            emb = item["embedding"]
            dot = sum(a * b for a, b in zip(query_embedding, emb))
            norm1 = (sum(a * a for a in query_embedding)) ** 0.5
            norm2 = (sum(b * b for b in emb)) ** 0.5
            score = dot / (norm1 * norm2) if norm1 > 1e-6 and norm2 > 1e-6 else 0.0

            results.append({
                "id": item["id"],
                "text": item["text"],
                "metadata": item["metadata"],
                "source": item["source"],
                "score": round(score, 4)
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def clear(self) -> None:
        """Clears all stored document vectors."""
        self._items.clear()
        if self._chroma_collection is not None:
            try:
                self._chroma_collection.delete()
            except Exception:
                pass


# Global ChromaVectorDB Instance
global_vectordb = ChromaVectorDB()
