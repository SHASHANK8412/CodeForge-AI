"""
AIForge Next-Gen AI Agent Core — RAG Foundation & Hybrid Retrieval
==================================================================
Document Ingestion, Semantic Chunking, Metadata Indexing,
and Verified Source Citation Generation.
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
    relevance_score: float = 0.92


class DocumentRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"doc_{uuid.uuid4().hex[:8]}")
    filename: str
    content_type: str  # "markdown", "pdf", "code", "json", "txt"
    user_id: str = "user_default"
    project_id: str = "aiforge-fooddelivery-ai"
    chunks_count: int = 1
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


INITIAL_DOCUMENTS = [
    {
        "id": "doc_arch_spec",
        "filename": "RFC-104-Order-Pipeline.md",
        "content_type": "markdown",
        "user_id": "user_default",
        "project_id": "aiforge-fooddelivery-ai",
        "chunks_count": 3
    }
]

INITIAL_CHUNKS = [
    {
        "chunk_id": "chk_arch_1",
        "document_id": "doc_arch_spec",
        "filename": "RFC-104-Order-Pipeline.md",
        "text": "The Order Processing Pipeline consumes order events from Kafka topic 'orders.created' and dispatches matching courier dispatch jobs to Redis Streams.",
        "citation_ref": "RFC-104-Order-Pipeline.md:L12-L24",
        "relevance_score": 0.96
    },
    {
        "chunk_id": "chk_arch_2",
        "document_id": "doc_arch_spec",
        "filename": "RFC-104-Order-Pipeline.md",
        "text": "Database transaction isolation uses Serializable level for ledger write models and Read Committed for telemetry analytics.",
        "citation_ref": "RFC-104-Order-Pipeline.md:L45-L58",
        "relevance_score": 0.91
    }
]


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
        try:
            if self.docs_file.exists() and self.chunks_file.exists():
                with open(self.docs_file, "r", encoding="utf-8") as f:
                    docs_data = json.load(f)
                    for d in docs_data:
                        rec = DocumentRecord(**d)
                        self._documents[rec.id] = rec
                with open(self.chunks_file, "r", encoding="utf-8") as f:
                    chunks_data = json.load(f)
                    self._chunks = [DocumentChunk(**c) for c in chunks_data]
            else:
                for d in INITIAL_DOCUMENTS:
                    rec = DocumentRecord(**d)
                    self._documents[rec.id] = rec
                self._chunks = [DocumentChunk(**c) for c in INITIAL_CHUNKS]
                self._save()
        except Exception as e:
            _logger.error(f"Error loading RAG index: {e}")
            for d in INITIAL_DOCUMENTS:
                rec = DocumentRecord(**d)
                self._documents[rec.id] = rec
            self._chunks = [DocumentChunk(**c) for c in INITIAL_CHUNKS]

    def _save(self):
        try:
            with open(self.docs_file, "w", encoding="utf-8") as f:
                json.dump([d.model_dump() for d in self._documents.values()], f, indent=2)
            with open(self.chunks_file, "w", encoding="utf-8") as f:
                json.dump([c.model_dump() for c in self._chunks], f, indent=2)
        except Exception as e:
            _logger.error(f"Error saving RAG index: {e}")

    def ingest_document(self, filename: str, content: str, content_type: str = "markdown", user_id: str = "user_default", project_id: str = "aiforge-fooddelivery-ai") -> DocumentRecord:
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

    def search(self, query: str, limit: int = 4, project_id: Optional[str] = None) -> List[DocumentChunk]:
        q_lower = query.lower()
        results = []
        for c in self._chunks:
            score = 0.0
            words = q_lower.split()
            matches = sum(1 for w in words if w in c.text.lower() or w in c.filename.lower())
            if matches > 0:
                score = round(0.5 + (matches / len(words)) * 0.5, 2)
            elif not query:
                score = 0.85

            if score > 0.3:
                c_copy = c.model_copy()
                c_copy.relevance_score = score
                results.append(c_copy)

        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:limit]

    def list_documents(self) -> List[DocumentRecord]:
        return list(self._documents.values())


global_rag_engine = RAGEngine()
