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
from datetime import datetime
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
    Persistent Memory Service managing 3-tier project memory:
    1. Project Memory (Architecture, Tech Stack, Auth, DB, Decisions, Conventions with superseding)
    2. Codebase Memory (Integrates with CodebaseIndexer, DependencyGraph, ImpactAnalyzer)
    3. Execution Memory (Runs, Test Failures, Successful Fixes, Approvals)
    """

    def __init__(self, store_path: Optional[str] = None):
        if store_path is None:
            mem_dir = Path(__file__).resolve().parent / "store"
            mem_dir.mkdir(parents=True, exist_ok=True)
            store_path = str(mem_dir / "memory_records.json")
        self.store_file = Path(store_path)
        self._project_memories_file = self.store_file.parent / "project_tier_memories.json"
        self._init_store()

    def _init_store(self) -> None:
        try:
            self.store_file.parent.mkdir(parents=True, exist_ok=True)
            if not self.store_file.exists():
                self.store_file.write_text("[]", encoding="utf-8")
            if not self._project_memories_file.exists():
                self._project_memories_file.write_text("{}", encoding="utf-8")
        except Exception as e:
            _logger.warning(f"Could not initialize memory files: {e}")

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

    def _load_tier_memories(self) -> Dict[str, Dict[str, Any]]:
        try:
            if not self._project_memories_file.exists():
                return {}
            content = self._project_memories_file.read_text(encoding="utf-8")
            return json.loads(content) if content.strip() else {}
        except Exception as e:
            _logger.warning(f"Failed to load project_tier_memories.json: {e}")
            return {}

    def _save_tier_memories(self, data: Dict[str, Dict[str, Any]]) -> None:
        try:
            self._project_memories_file.parent.mkdir(parents=True, exist_ok=True)
            self._project_memories_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            _logger.warning(f"Failed to save project_tier_memories.json: {e}")

    # =========================================================================
    # Tier 1: Project Memory Management with Conflict Resolution (Superseding)
    # =========================================================================

    def save_project_memory(
        self,
        project_id: str,
        memory_type: str,
        key: str,
        value: Any,
        source: str = "AGENT",
        importance: str = "HIGH",
        tags: Optional[List[str]] = None,
        supersedes_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Saves or updates a project-level architectural memory item.
        If a memory with the same key exists or supersedes_key is specified, marks old item as SUPERSEDED.
        """
        clean_key = sanitize_memory_content(key)
        clean_value = sanitize_memory_content(json.dumps(value) if isinstance(value, (dict, list)) else str(value))
        all_data = self._load_tier_memories()
        proj_mem = all_data.setdefault(project_id, {})

        mem_id = f"mem_{hashlib.md5(f'{project_id}_{memory_type}_{clean_key}_{datetime.now().timestamp()}'.encode()).hexdigest()[:12]}"
        now_iso = datetime.now().isoformat()

        # Handle Conflict Resolution / Superseding
        target_supersede = supersedes_key or clean_key
        for old_id, old_item in proj_mem.items():
            if old_item.get("key") == target_supersede and old_item.get("status") == "ACTIVE":
                old_item["status"] = "SUPERSEDED"
                old_item["superseded_by"] = mem_id
                old_item["updated_at"] = now_iso
                _logger.info(f"Memory conflict resolved: '{old_item.get('key')}' marked SUPERSEDED by '{mem_id}'")

        new_item = {
            "id": mem_id,
            "project_id": project_id,
            "memory_type": memory_type.upper(),
            "key": clean_key,
            "value": json.loads(clean_value) if (clean_value.startswith("{") or clean_value.startswith("[")) else clean_value,
            "source": source.upper(),
            "importance": importance.upper(),
            "status": "ACTIVE",
            "supersedes_id": target_supersede if target_supersede != clean_key else None,
            "superseded_by": None,
            "tags": tags or [],
            "created_at": now_iso,
            "updated_at": now_iso,
        }

        proj_mem[mem_id] = new_item
        self._save_tier_memories(all_data)
        _logger.info(f"Saved Project Memory '{clean_key}' ({memory_type}) for project '{project_id}'")
        return new_item

    def get_active_memories(self, project_id: str, memory_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all ACTIVE non-superseded project memories."""
        all_data = self._load_tier_memories()
        proj_mem = all_data.get(project_id, {})
        active = [m for m in proj_mem.values() if m.get("status") == "ACTIVE"]

        if memory_type:
            m_type_clean = memory_type.upper()
            active = [m for m in active if m.get("memory_type") == m_type_clean]

        active.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return active

    def get_all_memories(self, project_id: str, include_superseded: bool = False) -> List[Dict[str, Any]]:
        """Returns memories for project_id with optional superseded history."""
        all_data = self._load_tier_memories()
        proj_mem = all_data.get(project_id, {})
        items = list(proj_mem.values())
        if not include_superseded:
            items = [m for m in items if m.get("status") == "ACTIVE"]
        items.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return items

    def delete_project_memory(self, project_id: str, memory_id: str) -> bool:
        """Deletes a memory item by ID."""
        all_data = self._load_tier_memories()
        proj_mem = all_data.get(project_id)
        if proj_mem and memory_id in proj_mem:
            del proj_mem[memory_id]
            self._save_tier_memories(all_data)
            return True
        return False

    def search_project_memories(self, project_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Searches active project memories by keyword."""
        active = self.get_active_memories(project_id)
        if not query.strip():
            return active[:top_k]

        q_terms = set(query.lower().split())
        scored = []
        for m in active:
            text = f"{m.get('key', '')} {m.get('memory_type', '')} {json.dumps(m.get('value', ''))}".lower()
            matches = sum(1 for term in q_terms if term in text)
            imp_boost = {"CRITICAL": 3.0, "HIGH": 2.0, "MEDIUM": 1.0, "LOW": 0.5}.get(m.get("importance"), 1.0)
            score = matches * imp_boost
            scored.append((score, m))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]

    # =========================================================================
    # Tier 2 & 3: Execution Memory & Backward-Compatible MemoryRecord API
    # =========================================================================

    def _compute_record_hash(self, rec: MemoryRecord) -> str:
        raw = f"{rec.project_id}:{rec.memory_type}:{rec.error_type}:{rec.technology}:{rec.root_cause}:{rec.fix}:{rec.content}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def store_memory(self, record: MemoryRecord) -> MemoryRecord:
        """Sanitizes, deduplicates, and stores a MemoryRecord in both persistent file and vector index."""
        try:
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
                records[existing_idx]["result"] = record.result
                records[existing_idx]["confidence"] = max(records[existing_idx].get("confidence", 0.5), record.confidence)
                records[existing_idx]["content"] = record.content
                records[existing_idx]["fix"] = record.fix
            else:
                records.append(rec_dict)

            self._save_records(records)

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
            _logger.warning(f"ProjectMemoryService.store_memory warning: {e}")

        return record

    def retrieve_relevant_memories(
        self,
        project_id: str = "",
        error_type: str = "",
        query_text: str = "",
        technology: str = "",
        top_k: int = 3
    ) -> List[MemoryRecord]:
        """Retrieves and ranks relevant memory records based on project matching, error type, and similarity."""
        try:
            records_data = self._load_records()
            if not records_data:
                return []

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
                if error_type and rec_err:
                    if error_type.lower() == rec_err.lower() or error_type.lower() in rec_err.lower() or rec_err.lower() in error_type.lower():
                        score += 50.0
                if technology and rec_tech:
                    tech_q_tokens = set(re.split(r"[\s,]+", technology.lower())) - {""}
                    tech_rec_tokens = set(re.split(r"[\s,]+", rec_tech.lower())) - {""}
                    if tech_q_tokens & tech_rec_tokens:
                        score += 50.0
                if rec_res == "PASS":
                    score += 10.0
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
            _logger.warning(f"ProjectMemoryService.retrieve_relevant_memories failed: {e}")
            return []


global_project_memory_service = ProjectMemoryService()

