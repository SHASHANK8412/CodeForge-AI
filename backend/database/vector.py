"""
AIForge Day 27 — Vector Storage Abstraction (pgvector & ChromaDB)
===================================================================
Provides abstract VectorStore interface with PostgresVectorStore and ChromaVectorStore implementations,
enforcing strict project_id isolation and vector dimension validation.
"""

import os
import json
import math
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from backend.rag.embedding_service import cosine_similarity

_logger = logging.getLogger("aiforge.database.vector")

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "384"))


class VectorStore(ABC):
    """
    Abstract Vector Storage Interface.
    """

    @abstractmethod
    def add(
        self,
        documents: List[Dict[str, Any]],
        embeddings: List[List[float]],
        project_id: str = "default_project"
    ) -> int:
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        project_id: str = "default_project",
        top_k: int = 5,
        document_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete(self, project_id: str, doc_id: Optional[str] = None) -> int:
        pass

    @abstractmethod
    def update(self, project_id: str, doc_id: str, updates: Dict[str, Any]) -> bool:
        pass


class ChromaVectorStore(VectorStore):
    """
    ChromaDB vector store implementation with project-level isolation.
    """

    def __init__(self, collection_name: str = "aiforge_knowledge"):
        self.collection_name = collection_name
        self._items: Dict[str, Dict[str, Any]] = {}
        self._chroma_collection = None

        try:
            import chromadb
            client = chromadb.Client()
            self._chroma_collection = client.get_or_create_collection(collection_name)
            _logger.info(f"[ChromaVectorStore] Initialized collection '{collection_name}'")
        except Exception as e:
            _logger.info(f"[ChromaVectorStore] ChromaDB fallback ({e})")

    def add(
        self,
        documents: List[Dict[str, Any]],
        embeddings: List[List[float]],
        project_id: str = "default_project"
    ) -> int:
        added_count = 0
        for doc, emb in zip(documents, embeddings):
            if len(emb) != EMBEDDING_DIMENSIONS:
                raise ValueError(
                    f"Vector dimension mismatch: expected {EMBEDDING_DIMENSIONS}, got {len(emb)}"
                )

            doc_id = doc.get("id", f"{project_id}_doc_{len(self._items)}")
            item = {
                "id": doc_id,
                "project_id": project_id,
                "text": doc.get("text", ""),
                "source": doc.get("source", "unknown"),
                "document_type": doc.get("document_type", "DOCUMENTATION"),
                "chunk_index": doc.get("chunk_index", 0),
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
                        metadatas=[{"project_id": project_id, "source": doc.get("source", "")}]
                    )
                except Exception:
                    pass

        return added_count

    def search(
        self,
        query_embedding: List[float],
        project_id: str = "default_project",
        top_k: int = 5,
        document_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        results = []
        doc_type_set = set(document_types) if document_types else None

        for doc_id, item in self._items.items():
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
                "score": round(score, 4),
                "metadata": item["metadata"]
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def delete(self, project_id: str, doc_id: Optional[str] = None) -> int:
        if doc_id:
            item = self._items.get(doc_id)
            if item and item.get("project_id") == project_id:
                del self._items[doc_id]
                return 1
            return 0

        to_del = [k for k, v in self._items.items() if v.get("project_id") == project_id]
        for k in to_del:
            del self._items[k]
        return len(to_del)

    def update(self, project_id: str, doc_id: str, updates: Dict[str, Any]) -> bool:
        item = self._items.get(doc_id)
        if item and item.get("project_id") == project_id:
            item.update(updates)
            return True
        return False


class PostgresVectorStore(VectorStore):
    """
    PostgreSQL + pgvector vector store implementation with strict project_id isolation.
    """

    def __init__(self, collection_name: str = "aiforge_knowledge"):
        self.collection_name = collection_name

    def add(
        self,
        documents: List[Dict[str, Any]],
        embeddings: List[List[float]],
        project_id: str = "default_project"
    ) -> int:
        from backend.database.connection import SessionLocal
        from backend.database.models import VectorEmbeddingModel

        db = SessionLocal()
        added_count = 0
        try:
            for doc, emb in zip(documents, embeddings):
                if len(emb) != EMBEDDING_DIMENSIONS:
                    raise ValueError(
                        f"Vector dimension mismatch: expected {EMBEDDING_DIMENSIONS}, got {len(emb)}"
                    )

                doc_id = doc.get("id", f"{project_id}_doc_{added_count}_{os.urandom(4).hex()}")
                record = VectorEmbeddingModel(
                    id=f"vec_{os.urandom(6).hex()}",
                    project_id=project_id,
                    collection_name=self.collection_name,
                    document_id=doc_id,
                    text=doc.get("text", ""),
                    metadata_json=json.dumps(doc),
                    embedding_json=json.dumps(emb)
                )
                db.add(record)
                added_count += 1

            db.commit()
            _logger.info(f"[PostgresVectorStore] Added {added_count} vector(s) for project '{project_id}'")
            return added_count
        except Exception as e:
            db.rollback()
            _logger.error(f"[PostgresVectorStore] Failed to add vectors: {e}")
            raise e
        finally:
            db.close()

    def search(
        self,
        query_embedding: List[float],
        project_id: str = "default_project",
        top_k: int = 5,
        document_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        from backend.database.connection import SessionLocal
        from backend.database.models import VectorEmbeddingModel

        db = SessionLocal()
        try:
            records = db.query(VectorEmbeddingModel).filter(
                VectorEmbeddingModel.project_id == project_id,
                VectorEmbeddingModel.collection_name == self.collection_name
            ).all()

            results = []
            doc_type_set = set(document_types) if document_types else None

            for rec in records:
                meta = json.loads(rec.metadata_json or "{}")
                doc_type = meta.get("document_type", "DOCUMENTATION")

                if doc_type_set and doc_type not in doc_type_set:
                    continue

                emb = json.loads(rec.embedding_json)
                score = cosine_similarity(query_embedding, emb)

                results.append({
                    "id": rec.document_id,
                    "project_id": rec.project_id,
                    "text": rec.text,
                    "source": meta.get("source", "unknown"),
                    "document_type": doc_type,
                    "score": round(score, 4),
                    "metadata": meta
                })

            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:top_k]
        finally:
            db.close()

    def delete(self, project_id: str, doc_id: Optional[str] = None) -> int:
        from backend.database.connection import SessionLocal
        from backend.database.models import VectorEmbeddingModel

        db = SessionLocal()
        try:
            query = db.query(VectorEmbeddingModel).filter(
                VectorEmbeddingModel.project_id == project_id,
                VectorEmbeddingModel.collection_name == self.collection_name
            )
            if doc_id:
                query = query.filter(VectorEmbeddingModel.document_id == doc_id)

            count = query.delete(synchronize_session=False)
            db.commit()
            return count
        except Exception as e:
            db.rollback()
            _logger.error(f"[PostgresVectorStore] Delete failed: {e}")
            return 0
        finally:
            db.close()

    def update(self, project_id: str, doc_id: str, updates: Dict[str, Any]) -> bool:
        from backend.database.connection import SessionLocal
        from backend.database.models import VectorEmbeddingModel

        db = SessionLocal()
        try:
            rec = db.query(VectorEmbeddingModel).filter(
                VectorEmbeddingModel.project_id == project_id,
                VectorEmbeddingModel.document_id == doc_id
            ).first()

            if not rec:
                return False

            meta = json.loads(rec.metadata_json or "{}")
            meta.update(updates)
            rec.metadata_json = json.dumps(meta)
            if "text" in updates:
                rec.text = updates["text"]

            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
        finally:
            db.close()


def get_vector_store(provider: str = "postgres", collection_name: str = "aiforge_knowledge") -> VectorStore:
    """Factory function for instantiating the vector store implementation."""
    if provider.lower() in ("postgres", "pgvector"):
        return PostgresVectorStore(collection_name=collection_name)
    return ChromaVectorStore(collection_name=collection_name)
