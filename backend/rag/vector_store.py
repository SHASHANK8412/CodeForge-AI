import math
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("aiforge.rag.vector_store")


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


class VectorStore:
    """
    VectorStore maintains embedding vectors and metadata for fast semantic search.
    Supports ChromaDB if installed, or high-performance in-memory vector indexing with cosine similarity.
    """

    def __init__(self, collection_name: str = "aiforge_knowledge"):
        self.collection_name = collection_name
        self._items: Dict[str, Dict[str, Any]] = {}
        self._chroma_collection = None

        try:
            import chromadb
            client = chromadb.Client()
            self._chroma_collection = client.get_or_create_collection(collection_name)
            logger.info(f"Initialized ChromaDB collection: '{collection_name}'")
        except Exception as e:
            logger.info(f"ChromaDB not initialized ({e}); using high-performance vector store.")

    def add_documents(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]) -> int:
        """
        Adds document chunks and their embedding vectors to the vector store.
        Each document item should have 'id', 'text', and 'source'.
        """
        added_count = 0
        for doc, emb in zip(documents, embeddings):
            doc_id = doc.get("id", f"doc_{len(self._items)}")
            item = {
                "id": doc_id,
                "text": doc.get("text", ""),
                "source": doc.get("source", "unknown"),
                "chunk_index": doc.get("chunk_index", 0),
                "embedding": emb
            }
            self._items[doc_id] = item
            added_count += 1

            if self._chroma_collection is not None:
                try:
                    self._chroma_collection.add(
                        ids=[doc_id],
                        embeddings=[emb],
                        documents=[doc.get("text", "")],
                        metadatas=[{"source": doc.get("source", "")}]
                    )
                except Exception:
                    pass

        logger.info(f"VectorStore added {added_count} chunk(s) to '{self.collection_name}'")
        return added_count

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Searches vector store for top_k documents most similar to query_embedding."""
        if not self._items:
            return []

        results = []
        for item_id, item in self._items.items():
            score = cosine_similarity(query_embedding, item["embedding"])
            results.append({
                "id": item["id"],
                "text": item["text"],
                "source": item["source"],
                "chunk_index": item["chunk_index"],
                "score": round(score, 4)
            })

        # Sort by similarity score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def delete_document(self, doc_id: str) -> bool:
        """Deletes a specific document chunk by ID."""
        if doc_id in self._items:
            del self._items[doc_id]
            return True
        return False

    def clear(self) -> None:
        """Clears all indexed vectors and documents."""
        self._items.clear()
        if self._chroma_collection is not None:
            try:
                self._chroma_collection.delete()
            except Exception:
                pass

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics on stored vectors and documents."""
        sources = set(item["source"] for item in self._items.values())
        return {
            "collection_name": self.collection_name,
            "total_chunks": len(self._items),
            "unique_documents": len(sources),
            "sources": list(sources)
        }
