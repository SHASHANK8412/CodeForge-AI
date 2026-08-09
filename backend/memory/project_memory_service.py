"""
AIForge Cross-Project Persistent Memory & Context Retrieval Service (Phase 10)
============================================================================
Provides structured memory storage, vector retrieval, secret sanitization,
deduplication, and fail-safe fallback logic for Planner, Architect, and Debugger.
"""

import re
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.execution.models import MemoryRecord
from backend.memory.vector_memory import global_vector_memory

_logger = logging.getLogger("aiforge.memory.project_memory_service")

SECRET_PATTERNS = [
    (r"(?i)(api[_-]?key|secret|password|passwd|auth[_-]?token|bearer)\s*[:=]\s*['\"]?([^'\"\s;]+)['\"]?", r"\1=[REDACTED_SECRET]"),
    (r"(?i)postgres(?:ql)?://[^\s'\"]+", r"[REDACTED_DATABASE_URL]"),
    (r"eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*", r"[REDACTED_TOKEN]")
]


def sanitize_memory_content(text: str) -> str:
    """
    Redacts sensitive credentials, API keys, passwords, and tokens from memory text.
    """
    if not text:
        return ""
    sanitized = str(text)
    for pat, repl in SECRET_PATTERNS:
        sanitized = re.sub(pat, repl, sanitized)
    return sanitized



class ProjectMemoryService:
    """
    Persistent Memory Service managing project facts, failure tracebacks,
    successful fixes, and engineering patterns.
    """

    def __init__(self, store_path: Optional[str] = None):
        if store_path is None:
            mem_dir = Path(__file__).resolve().parent / "store"
            mem_dir.mkdir(parents=True, exist_ok=True)
            store_path = str(mem_dir / "memory_records.json")
        self.store_file = Path(store_path)
        self._init_store()

    def _init_store(self) -> None:
        if not self.store_file.exists():
            try:
                self.store_file.parent.mkdir(parents=True, exist_ok=True)
                self.store_file.write_text("[]", encoding="utf-8")
            except Exception as e:
                _logger.warning(f"Could not initialize memory_records.json: {e}")


    def _load_records(self) -> List[Dict[str, Any]]:
        try:
            if not self.store_file.exists():
                return []
            content = self.store_file.read_text(encoding="utf-8")
            return json.loads(content) if content.strip() else []
        except Exception as e:
            _logger.warning(f"Failed to load memory_records.json: {e}")
            return []

    def _save_records(self, records: List[Dict[str, Any]]) -> None:
        try:
            self.store_file.parent.mkdir(parents=True, exist_ok=True)
            self.store_file.write_text(json.dumps(records, indent=2), encoding="utf-8")
        except Exception as e:
            _logger.warning(f"Failed to save memory_records.json: {e}")

    def _compute_record_hash(self, rec: MemoryRecord) -> str:
        raw = f"{rec.project_id}:{rec.memory_type}:{rec.error_type}:{rec.technology}:{rec.root_cause}:{rec.fix}:{rec.content}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()


    def store_memory(self, record: MemoryRecord) -> MemoryRecord:
        """
        Sanitizes, deduplicates, and stores a MemoryRecord in both persistent file and vector index.
        """
        try:
            # 1. Sanitize text fields
            record.content = sanitize_memory_content(record.content)
            record.root_cause = sanitize_memory_content(record.root_cause)
            record.fix = sanitize_memory_content(record.fix)

            rec_dict = record.model_dump() if hasattr(record, "model_dump") else record.dict()
            rec_hash = self._compute_record_hash(record)
            rec_dict["hash"] = rec_hash

            records = self._load_records()
            existing_idx = None
            for idx, item in enumerate(records):
                if item.get("hash") == rec_hash or item.get("memory_id") == record.memory_id:
                    existing_idx = idx
                    break

            if existing_idx is not None:
                # Update existing record
                records[existing_idx]["result"] = record.result
                records[existing_idx]["confidence"] = max(records[existing_idx].get("confidence", 0.5), record.confidence)
                records[existing_idx]["content"] = record.content
                records[existing_idx]["fix"] = record.fix
            else:
                records.append(rec_dict)

            self._save_records(records)

            # 2. Add to Vector Memory Store for semantic search
            search_text = f"{record.error_type} {record.technology} {record.content} {record.root_cause}"
            global_vector_memory.add_vector(
                doc_id=record.memory_id,
                text=search_text,
                metadata={
                    "memory_id": record.memory_id,
                    "project_id": record.project_id,
                    "error_type": record.error_type,
                    "technology": record.technology,
                    "result": record.result,
                    "fix": record.fix
                }
            )
            _logger.info(f"Stored MemoryRecord '{record.memory_id}' for project '{record.project_id}'")
        except Exception as e:
            _logger.warning(f"ProjectMemoryService.store_memory encountered warning (continuing without error): {e}")

        return record

    def retrieve_relevant_memories(
        self,
        project_id: str = "",
        error_type: str = "",
        query_text: str = "",
        technology: str = "",
        top_k: int = 3
    ) -> List[MemoryRecord]:
        """
        Retrieves and ranks relevant memory records based on project matching, error type, tech stack, and vector similarity.
        """
        try:
            records_data = self._load_records()
            if not records_data:
                return []

            # 1. Query vector store for semantic similarity scores
            search_query = f"{error_type} {technology} {query_text}".strip()
            vector_hits = global_vector_memory.search_similar(search_query, top_k=top_k * 4) if search_query else []
            sim_scores = {hit["id"]: max(0.0, float(hit.get("similarity_score", 0.0))) for hit in vector_hits}

            scored_records = []
            for item in records_data:
                score = 0.0
                rec_proj = item.get("project_id", "")
                rec_err = item.get("error_type", "")
                rec_tech = item.get("technology", "")
                rec_res = item.get("result", "PASS")
                mem_id = item.get("memory_id", "")

                # Project Isolation / Same Project Priority
                if project_id and rec_proj == project_id:
                    score += 100.0
                # Error type matching
                if error_type and rec_err:
                    if error_type.lower() == rec_err.lower() or error_type.lower() in rec_err.lower() or rec_err.lower() in error_type.lower():
                        score += 50.0

                # Tech stack matching
                if technology and rec_tech:
                    tech_q_tokens = set(re.split(r"[\s,]+", technology.lower())) - {""}
                    tech_rec_tokens = set(re.split(r"[\s,]+", rec_tech.lower())) - {""}
                    if tech_q_tokens & tech_rec_tokens:
                        score += 50.0


                # Prioritize successful fixes over failed ones
                if rec_res == "PASS":
                    score += 10.0

                # Semantic Similarity Weight
                score += sim_scores.get(mem_id, 0.0) * 1.0

                scored_records.append((score, item))

            scored_records.sort(key=lambda x: x[0], reverse=True)
            top_records = [item for sc, item in scored_records[:top_k] if sc > 0.1 or len(scored_records) <= top_k]

            result_models = []
            for item in top_records:
                item_copy = dict(item)
                item_copy.pop("hash", None)
                result_models.append(MemoryRecord(**item_copy))

            return result_models
        except Exception as e:
            _logger.warning(f"ProjectMemoryService.retrieve_relevant_memories failed gracefully: {e}")
            return []


global_project_memory_service = ProjectMemoryService()
