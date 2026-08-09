import math
import logging
from typing import Dict, Any, List, Optional, Set

from backend.rag.embedding_service import cosine_similarity

logger = logging.getLogger("aiforge.rag.vector_store")


class VectorStore:
    """
    VectorStore maintains embedding vectors and metadata with strict project-level isolation.
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

    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        embeddings: List[List[float]],
        project_id: str = "default_project"
    ) -> int:
        """
        Adds document chunks and their embedding vectors to the vector store under project_id.
        """
        added_count = 0
        for doc, emb in zip(documents, embeddings):
            doc_id = doc.get("id", f"{project_id}_doc_{len(self._items)}")
            item = {
                "id": doc_id,
                "project_id": project_id,
                "text": doc.get("text", ""),
                "source": doc.get("source", "unknown"),
                "document_type": doc.get("document_type", "DOCUMENTATION"),
                "chunk_index": doc.get("chunk_index", 0),
                "heading": doc.get("heading", ""),
                "symbol": doc.get("symbol", ""),
                "language": doc.get("language", ""),
                "line_start": doc.get("line_start"),
                "line_end": doc.get("line_end"),
                "version": doc.get("version", "1.0"),
                "embedding": emb,
                "metadata": doc
            }
            self._items[doc_id] = item
            added_count += 1

            if self._chroma_collection is not None:
                try:
                    self._chroma_collection.add(
                        ids=[doc_id],
                        embeddings=[emb],
                        documents=[doc.get("text", "")],
                        metadatas=[{
                            "project_id": project_id,
                            "source": doc.get("source", ""),
                            "document_type": doc.get("document_type", "DOCUMENTATION")
                        }]
                    )
                except Exception:
                    pass

        logger.info(f"VectorStore added {added_count} chunk(s) for project '{project_id}'")
        return added_count

    def search(
        self,
        query_embedding: List[float],
        project_id: str = "default_project",
        top_k: int = 5,
        document_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Searches vector store for top_k documents belonging to project_id.
        """
        if not self._items:
            return []

        results = []
        doc_type_set = set(document_types) if document_types else None

        for item_id, item in self._items.items():
            # Strict Project Isolation Filter
            if item.get("project_id") != project_id:
                continue

            if doc_type_set and item.get("document_type") not in doc_type_set:
                continue

            score = cosine_similarity(query_embedding, item["embedding"])
            results.append({
                "id": item["id"],
                "project_id": item["project_id"],
                "text": item["text"],
                "source": item["source"],
                "document_type": item["document_type"],
                "chunk_index": item["chunk_index"],
                "heading": item.get("heading", ""),
                "symbol": item.get("symbol", ""),
                "language": item.get("language", ""),
                "line_start": item.get("line_start"),
                "line_end": item.get("line_end"),
                "score": round(score, 4),
                "metadata": item["metadata"]
            })

        # Sort by similarity score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def delete_project(self, project_id: str) -> int:
        """Deletes all indexed vectors and documents associated with project_id."""
        to_delete = [doc_id for doc_id, item in self._items.items() if item.get("project_id") == project_id]
        for doc_id in to_delete:
            del self._items[doc_id]

        if self._chroma_collection is not None and to_delete:
            try:
                self._chroma_collection.delete(ids=to_delete)
            except Exception:
                pass

        logger.info(f"VectorStore deleted {len(to_delete)} chunk(s) for project '{project_id}'")
        return len(to_delete)

    def delete_document(self, project_id: str, doc_id: str) -> bool:
        """Deletes a specific document chunk by ID enforcing project_id match."""
        item = self._items.get(doc_id)
        if item and item.get("project_id") == project_id:
            del self._items[doc_id]
            if self._chroma_collection is not None:
                try:
                    self._chroma_collection.delete(ids=[doc_id])
                except Exception:
                    pass
            return True
        return False

    def update_document(self, project_id: str, doc_id: str, updates: Dict[str, Any]) -> bool:
        """Updates metadata or text for an existing document chunk."""
        item = self._items.get(doc_id)
        if item and item.get("project_id") == project_id:
            item.update(updates)
            return True
        return False

    def clear(self) -> None:
        """Clears all indexed vectors and documents across all projects."""
        self._items.clear()
        if self._chroma_collection is not None:
            try:
                self._chroma_collection.delete()
            except Exception:
                pass

    def get_stats(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Returns statistics on stored vectors and documents."""
        items = list(self._items.values())
        if project_id:
            items = [item for item in items if item.get("project_id") == project_id]

        sources = set(item["source"] for item in items)
        return {
            "collection_name": self.collection_name,
            "project_id": project_id or "all",
            "total_chunks": len(items),
            "unique_documents": len(sources),
            "sources": list(sources)
        }


global_vector_store = VectorStore()
