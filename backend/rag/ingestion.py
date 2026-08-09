"""
AIForge V2 — Day 13 Document & Repository Ingestion Pipeline
Handles structure-aware document chunking, code symbol chunking, secret redaction,
incremental indexing, hash versioning, and source deletion.
"""
import os
import re
import time
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from backend.rag.models import RetrievalDomain, SourceRecord, ChunkRecord
from backend.rag.config import global_rag_config
from backend.rag.embedding_service import global_embedding_service
from backend.repository.indexer import global_repository_indexer

logger = logging.getLogger("aiforge.rag.ingestion")

# Day 11 Secret Redaction Patterns
SECRET_PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "[REDACTED_AWS_KEY]"),
    (r"ghp_[A-Za-z0-9_]{36,255}", "[REDACTED_GITHUB_TOKEN]"),
    (r"-----\s*BEGIN\s+.*PRIVATE\s+KEY\s*-----[\s\S]*?-----\s*END\s+.*PRIVATE\s+KEY\s*-----", "[REDACTED_PRIVATE_KEY]"),
    (r"(?i)(api_key|secret_key|access_token|bearer_token)\s*=\s*['\"][A-Za-z0-9_\-\.]{16,}['\"]", r"\1='[REDACTED_SECRET]'"),
]


def redact_secrets(text: str) -> str:
    """Redacts plaintext API keys, AWS credentials, and tokens from text prior to embedding/indexing."""
    if not text:
        return ""
    sanitized = text
    for pattern, replacement in SECRET_PATTERNS:
        sanitized = re.sub(pattern, replacement, sanitized)
    return sanitized


class DocumentIngestionPipeline:
    """
    Document and Repository Ingestion Pipeline for Day 13.
    LOAD -> NORMALIZE -> EXTRACT STRUCTURE -> CHUNK -> REDACT -> EMBED -> INDEX -> VERIFY
    """

    def __init__(self):
        self.sources: Dict[str, SourceRecord] = {}
        self.chunks: Dict[str, ChunkRecord] = {}
        self.source_chunks: Dict[str, List[str]] = {}  # source_id -> [chunk_id]
        self.embedding_service = global_embedding_service

    def ingest_document(
        self,
        filepath_or_name: str,
        content: str,
        domain: RetrievalDomain = RetrievalDomain.DOCUMENT,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[SourceRecord, List[ChunkRecord]]:
        """Ingests a document with structure-aware chunking, secret redaction, and incremental versioning."""
        meta = metadata or {}
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        source_id = f"src_{hashlib.md5(filepath_or_name.encode('utf-8')).hexdigest()[:12]}"

        # Check existing version
        if source_id in self.sources:
            existing = self.sources[source_id]
            if existing.content_hash == content_hash:
                logger.info(f"Ingestion skipped: source '{filepath_or_name}' unchanged.")
                existing_chunks = [self.chunks[cid] for cid in self.source_chunks.get(source_id, []) if cid in self.chunks]
                return existing, existing_chunks
            else:
                # Remove old chunks for incremental update
                self.delete_source(source_id)

        source_record = SourceRecord(
            source_id=source_id,
            source_type=Path(filepath_or_name).suffix.lstrip(".").lower() or "txt",
            name=filepath_or_name,
            version=str(meta.get("version", "1.0")),
            content_hash=content_hash,
            created_at=time.time(),
            updated_at=time.time(),
            metadata=meta
        )

        # 1. Structure-Aware Chunking
        raw_chunks = self._chunk_document_structure(filepath_or_name, content, domain)

        # 2. Secret Redaction & Chunk Building
        chunk_records: List[ChunkRecord] = []
        cids: List[str] = []

        for idx, (chunk_text, chunk_meta) in enumerate(raw_chunks):
            safe_text = redact_secrets(chunk_text)
            c_hash = hashlib.sha256(safe_text.encode("utf-8")).hexdigest()
            cid = f"{source_id}_chunk_{idx}"
            chunk_meta["source"] = filepath_or_name
            chunk_meta["path"] = filepath_or_name

            c_record = ChunkRecord(
                chunk_id=cid,
                source_id=source_id,
                domain=domain,
                text=safe_text,
                metadata=chunk_meta,
                content_hash=c_hash,
                position=idx,
                token_count=len(safe_text.split()),
                document_id=source_id,
                path=filepath_or_name,
                page=chunk_meta.get("page"),
                section=chunk_meta.get("section"),
                heading=chunk_meta.get("heading")
            )
            self.chunks[cid] = c_record
            chunk_records.append(c_record)
            cids.append(cid)

        self.sources[source_id] = source_record
        self.source_chunks[source_id] = cids

        # 3. Generate Batch Embeddings
        texts = [c.text for c in chunk_records]
        vectors = self.embedding_service.get_batch_embeddings(texts)
        for c_rec, vec in zip(chunk_records, vectors):
            c_rec.metadata["embedding"] = vec

        logger.info(f"Ingested '{filepath_or_name}' into {len(chunk_records)} chunk(s).")
        return source_record, chunk_records

    def ingest_repository_file(
        self,
        rel_path: str,
        content: str,
        repo_id: str = "main_repo",
        symbols_info: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[SourceRecord, List[ChunkRecord]]:
        """Ingests a repository code file using symbol-aware chunking and secret redaction."""
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        source_id = f"repo_{repo_id}_{hashlib.md5(rel_path.encode('utf-8')).hexdigest()[:12]}"

        if source_id in self.sources:
            if self.sources[source_id].content_hash == content_hash:
                existing_chunks = [self.chunks[cid] for cid in self.source_chunks.get(source_id, []) if cid in self.chunks]
                return self.sources[source_id], existing_chunks
            else:
                self.delete_source(source_id)

        source_record = SourceRecord(
            source_id=source_id,
            source_type="code",
            name=rel_path,
            version="1.0",
            content_hash=content_hash,
            created_at=time.time(),
            updated_at=time.time(),
            metadata={"repository_id": repo_id, "path": rel_path}
        )

        # Code-aware symbol chunking
        raw_chunks = self._chunk_code_symbols(rel_path, content, symbols_info)

        chunk_records: List[ChunkRecord] = []
        cids: List[str] = []

        for idx, (chunk_text, chunk_meta) in enumerate(raw_chunks):
            safe_text = redact_secrets(chunk_text)
            c_hash = hashlib.sha256(safe_text.encode("utf-8")).hexdigest()
            cid = f"{source_id}_chunk_{idx}"
            chunk_meta["source"] = rel_path
            chunk_meta["path"] = rel_path

            c_record = ChunkRecord(
                chunk_id=cid,
                source_id=source_id,
                domain=RetrievalDomain.REPOSITORY,
                text=safe_text,
                metadata=chunk_meta,
                content_hash=c_hash,
                position=idx,
                token_count=len(safe_text.split()),
                repository_id=repo_id,
                path=rel_path,
                symbol=chunk_meta.get("symbol"),
                language=chunk_meta.get("language"),
                line_start=chunk_meta.get("line_start"),
                line_end=chunk_meta.get("line_end")
            )
            self.chunks[cid] = c_record
            chunk_records.append(c_record)
            cids.append(cid)

        self.sources[source_id] = source_record
        self.source_chunks[source_id] = cids

        texts = [c.text for c in chunk_records]
        vectors = self.embedding_service.get_batch_embeddings(texts)
        for c_rec, vec in zip(chunk_records, vectors):
            c_rec.metadata["embedding"] = vec

        return source_record, chunk_records

    def delete_source(self, source_id: str) -> bool:
        """Safely deletes all indexed chunks associated with a source."""
        if source_id in self.source_chunks:
            for cid in self.source_chunks[source_id]:
                if cid in self.chunks:
                    del self.chunks[cid]
            del self.source_chunks[source_id]

        if source_id in self.sources:
            del self.sources[source_id]
            return True
        return False

    def clear(self) -> None:
        """Clears all ingested sources and chunks."""
        self.sources.clear()
        self.chunks.clear()
        self.source_chunks.clear()

    # --- Private Chunking Helpers ---
    def _chunk_document_structure(
        self, filename: str, text: str, domain: RetrievalDomain
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """Chunks Markdown/PDF/DOCX/TXT text by sections, headings, or paragraph boundaries."""
        if not text or not text.strip():
            return []

        chunks: List[Tuple[str, Dict[str, Any]]] = []
        lines = text.splitlines()
        current_heading = "General"
        current_block: List[str] = []
        current_lines_count = 0

        target_words = global_rag_config.RAG_CHUNK_TARGET_TOKENS

        for line in lines:
            # Check for Markdown heading
            if line.startswith("#"):
                if current_block:
                    block_text = "\n".join(current_block).strip()
                    if block_text:
                        chunks.append((block_text, {"heading": current_heading, "section": current_heading}))
                    current_block = []
                current_heading = line.lstrip("#").strip()

            current_block.append(line)
            current_words = len(" ".join(current_block).split())
            if current_words >= target_words:
                block_text = "\n".join(current_block).strip()
                if block_text:
                    chunks.append((block_text, {"heading": current_heading, "section": current_heading}))
                current_block = []

        if current_block:
            block_text = "\n".join(current_block).strip()
            if block_text:
                chunks.append((block_text, {"heading": current_heading, "section": current_heading}))

        return chunks if chunks else [(text.strip(), {"heading": "General"})]

    def _chunk_code_symbols(
        self, rel_path: str, code: str, symbols_info: Optional[List[Dict[str, Any]]] = None
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """Chunks source code aligned with classes, functions, routes, or logical blocks."""
        chunks: List[Tuple[str, Dict[str, Any]]] = []
        ext = Path(rel_path).suffix.lstrip(".").lower()

        if symbols_info:
            lines = code.splitlines()
            for sym in symbols_info:
                s_name = sym.get("name")
                s_type = sym.get("type", "symbol")
                start_l = max(1, sym.get("line", 1))
                end_l = min(len(lines), start_l + 30)
                snippet = "\n".join(lines[start_l - 1:end_l]).strip()
                if snippet:
                    chunks.append((
                        snippet,
                        {
                            "symbol": s_name,
                            "symbol_type": s_type,
                            "path": rel_path,
                            "language": ext,
                            "line_start": start_l,
                            "line_end": end_l
                        }
                    ))
            if chunks:
                return chunks

        # Fallback line-based block chunking for code
        lines = code.splitlines()
        block_size = 40
        for i in range(0, len(lines), block_size - 10):
            sub_lines = lines[i:i + block_size]
            snippet = "\n".join(sub_lines).strip()
            if snippet:
                chunks.append((
                    snippet,
                    {
                        "path": rel_path,
                        "language": ext,
                        "line_start": i + 1,
                        "line_end": i + len(sub_lines)
                    }
                ))

        return chunks if chunks else [(code.strip(), {"path": rel_path, "language": ext, "line_start": 1, "line_end": len(lines)})]


# Global Ingestion Pipeline Singleton
global_ingestion_pipeline = DocumentIngestionPipeline()
