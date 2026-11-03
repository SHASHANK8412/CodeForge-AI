"""
AIForge Next-Gen AI Agent Core — RAG Foundation & Hybrid Retrieval
==================================================================
Document Ingestion, Semantic Chunking, Metadata Indexing,
and source citations for the documents a user uploads (no built-in sample documents).
"""

import time
import uuid
import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from pathlib import Path

_logger = logging.getLogger("aiforge.ai_core.rag")


class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    text: str
    citation_ref: str
    relevance_score: float = 0.0


class DocumentRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"doc_{uuid.uuid4().hex[:8]}")
    filename: str
    content_type: str  # "markdown", "pdf", "code", "json", "txt"
    user_id: str
    project_id: Optional[str] = None
    chunks_count: int = 1
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


class RAGEngine:
    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            self.storage_dir = Path(__file__).resolve().parent.parent / "data" / "rag_index"

        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.docs_file = self.storage_dir / "documents.json"
        self.chunks_file = self.storage_dir / "chunks.json"
        self._documents: Dict[str, DocumentRecord] = {}
        self._chunks: List[DocumentChunk] = []
        self._load()

    def _load(self):
        if not (self.docs_file.exists() and self.chunks_file.exists()):
            return
        try:
            with open(self.docs_file, "r", encoding="utf-8") as f:
                for d in json.load(f):
                    if not d.get("user_id") or d.get("user_id") == "user_default":
                        continue          # sample documents from earlier versions belong to nobody
                    rec = DocumentRecord(**d)
                    self._documents[rec.id] = rec
            with open(self.chunks_file, "r", encoding="utf-8") as f:
                self._chunks = [DocumentChunk(**c) for c in json.load(f) if c.get("document_id") in self._documents]
        except Exception as e:
            _logger.error(f"Error loading RAG index: {e}")

    def _save(self):
        try:
            with open(self.docs_file, "w", encoding="utf-8") as f:
                json.dump([d.model_dump() for d in self._documents.values()], f, indent=2)
            with open(self.chunks_file, "w", encoding="utf-8") as f:
                json.dump([c.model_dump() for c in self._chunks], f, indent=2)
        except Exception as e:
            _logger.error(f"Error saving RAG index: {e}")

    def ingest_document(self, filename: str, content: str, user_id: str, content_type: str = "markdown",
                        project_id: Optional[str] = None) -> DocumentRecord:
        doc = DocumentRecord(
            filename=filename,
            content_type=content_type,
            user_id=user_id,
            project_id=project_id,
            chunks_count=1
        )
        # Simple semantic chunking
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [content.strip()]
        
        doc.chunks_count = len(paragraphs)
        self._documents[doc.id] = doc

        for idx, p in enumerate(paragraphs):
            chunk = DocumentChunk(
                chunk_id=f"chk_{uuid.uuid4().hex[:8]}",
                document_id=doc.id,
                filename=filename,
                text=p,
                citation_ref=f"{filename}:P{idx+1}",
                relevance_score=1.0
            )
            self._chunks.append(chunk)

        self._save()
        return doc

    def search(self, query: str, limit: int = 4, project_id: Optional[str] = None,
               user_id: Optional[str] = None) -> List[DocumentChunk]:
        """Keyword search over the chunks of one user's documents (of every user when user_id is None)."""
        words = query.lower().split()
        if not words:
            return []
        results = []
        for c in self._chunks:
            doc = self._documents.get(c.document_id)
            if doc is None or (user_id is not None and doc.user_id != user_id):
                continue
            if project_id and doc.project_id and doc.project_id != project_id:
                continue
            text = c.text.lower()
            matches = sum(1 for w in words if w in text or w in c.filename.lower())
            if matches:
                c_copy = c.model_copy()
                c_copy.relevance_score = round(matches / len(words), 2)
                results.append(c_copy)
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:limit]

    def list_documents(self, user_id: str) -> List[DocumentRecord]:
        return [d for d in self._documents.values() if d.user_id == user_id]


global_rag_engine = RAGEngine()
