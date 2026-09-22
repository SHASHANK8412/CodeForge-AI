import os
import json
import time
import secrets
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set

from backend.memory.models import ProjectMemory, DecisionRecord, MemoryType, ImportanceLevel

logger = logging.getLogger("aiforge.memory.long_term")

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_MEMORY_FILE = _DATA_DIR / "projects_memory_v2.json"
_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Secret keys to strip before storing memory
SECRET_KEYWORDS: Set[str] = {
    "password", "secret", "api_key", "apikey", "access_token",
    "private_key", "jwt_secret", "database_url", "db_password", "bearer"
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sanitize_value(val: Any) -> Any:
    """Removes sensitive keys or values from memory data."""
    if isinstance(val, dict):
        sanitized = {}
        for k, v in val.items():
            if any(s in k.lower() for s in SECRET_KEYWORDS):
                sanitized[k] = "[REDACTED_SECRET]"
            else:
                sanitized[k] = _sanitize_value(v)
        return sanitized
    elif isinstance(val, list):
        return [_sanitize_value(item) for item in val]
    elif isinstance(val, str):
        val_lower = val.lower()
        if any(f"{s}=" in val_lower or f"{s}:" in val_lower for s in SECRET_KEYWORDS):
            return "[REDACTED_SENSITIVE_STRING]"
        return val
    return val


class LongTermMemory:
    """
    LongTermMemory manages persistent long-term storage for completed and ongoing projects,
    user preferences, architecture decisions, requirements, and generated code files across sessions.
    """

    def __init__(self, storage_file: Path = _MEMORY_FILE):
        self.storage_file = storage_file
        # Structure: { project_id: { "memories": { mem_id: dict }, "decisions": { dec_id: dict }, "meta": dict } }
        self.data: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if self.storage_file.exists():
            try:
                raw = json.loads(self.storage_file.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self.data = raw
            except Exception as e:
                logger.warning(f"Could not load long term memory from file: {e}")
                self.data = {}

    def _save(self) -> None:
        try:
            self.storage_file.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Could not save long term memory to file: {e}")

    def _ensure_project(self, project_id: str) -> Dict[str, Any]:
        if project_id not in self.data:
            self.data[project_id] = {
                "memories": {},
                "decisions": {},
                "meta": {
                    "project_id": project_id,
                    "created_at": _now_iso(),
                    "updated_at": _now_iso()
                }
            }
        return self.data[project_id]

    def save_memory(
        self,
        project_id: str,
        memory_type: MemoryType | str,
        key: str,
        value: Any,
        source_agent: str,
        importance: ImportanceLevel | str = ImportanceLevel.MEDIUM,
        generation_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> ProjectMemory:
        proj = self._ensure_project(project_id)
        now = _now_iso()

        # Sanitize value to prevent secrets leakage
        clean_value = _sanitize_value(value)

        m_type = memory_type if isinstance(memory_type, MemoryType) else MemoryType(str(memory_type).split(".")[-1])
        imp_level = importance if isinstance(importance, ImportanceLevel) else ImportanceLevel(str(importance).split(".")[-1])

        # Check if memory with same key and type exists, update it
        existing_id = None
        for m_id, m_dict in proj["memories"].items():
            if m_dict.get("memory_type") == m_type.value and m_dict.get("key") == key:
                existing_id = m_id
                break

        mem_id = existing_id or f"mem_{secrets.token_urlsafe(8)}"

        mem = ProjectMemory(
            id=mem_id,
            project_id=project_id,
            generation_id=generation_id,
            user_id=user_id,
            memory_type=m_type,
            key=key,
            value=clean_value,
            source_agent=source_agent,
            importance=imp_level,
            created_at=proj["memories"].get(mem_id, {}).get("created_at", now),
            updated_at=now
        )

        proj["memories"][mem_id] = mem.model_dump()
        proj["meta"]["updated_at"] = now
        self._save()
        logger.info(f"LongTermMemory saved memory '{key}' ({m_type.value}) for project '{project_id}'")
        return mem

    def save_decision(
        self,
        project_id: str,
        decision: str,
        reason: str,
        agent: str,
        importance: ImportanceLevel | str = ImportanceLevel.HIGH,
        generation_id: Optional[str] = None
    ) -> DecisionRecord:
        proj = self._ensure_project(project_id)
        now = _now_iso()

        imp_level = importance if isinstance(importance, ImportanceLevel) else ImportanceLevel(str(importance).split(".")[-1])

        dec_id = f"dec_{secrets.token_urlsafe(8)}"
        record = DecisionRecord(
            id=dec_id,
            project_id=project_id,
            generation_id=generation_id,
            decision=_sanitize_value(decision),
            reason=_sanitize_value(reason),
            agent=agent,
            timestamp=now,
            importance=imp_level
        )

        proj["decisions"][dec_id] = record.model_dump()
        proj["meta"]["updated_at"] = now
        self._save()
        logger.info(f"LongTermMemory saved decision '{decision[:30]}...' for project '{project_id}'")
        return record

    def get_memories(
        self,
        project_id: str,
        memory_type: Optional[MemoryType | str] = None,
        importance: Optional[ImportanceLevel | str] = None
    ) -> List[ProjectMemory]:
        proj = self.data.get(project_id, {})
        memories_dict = proj.get("memories", {})
        results = []

        for m_dict in memories_dict.values():
            if memory_type and m_dict.get("memory_type") != str(memory_type):
                continue
            if importance and m_dict.get("importance") != str(importance):
                continue
            try:
                results.append(ProjectMemory(**m_dict))
            except Exception:
                pass

        results.sort(key=lambda m: m.updated_at, reverse=True)
        return results

    def get_decisions(self, project_id: str) -> List[DecisionRecord]:
        proj = self.data.get(project_id, {})
        dec_dict = proj.get("decisions", {})
        results = []

        for d_dict in dec_dict.values():
            try:
                results.append(DecisionRecord(**d_dict))
            except Exception:
                pass

        results.sort(key=lambda d: d.timestamp, reverse=True)
        return results

    def get_memory(self, project_id: str, memory_id: str) -> Optional[ProjectMemory]:
        proj = self.data.get(project_id, {})
        m_dict = proj.get("memories", {}).get(memory_id)
        if m_dict:
            return ProjectMemory(**m_dict)
        return None

    def update_memory(self, project_id: str, memory_id: str, updates: Dict[str, Any]) -> Optional[ProjectMemory]:
        proj = self.data.get(project_id)
        if not proj or memory_id not in proj.get("memories", {}):
            return None

        m_dict = proj["memories"][memory_id]
        if "value" in updates:
            updates["value"] = _sanitize_value(updates["value"])

        m_dict.update(updates)
        m_dict["updated_at"] = _now_iso()
        proj["meta"]["updated_at"] = _now_iso()
        self._save()
        return ProjectMemory(**m_dict)

    def delete_memory(self, project_id: str, memory_id: str) -> bool:
        proj = self.data.get(project_id)
        if proj and memory_id in proj.get("memories", {}):
            del proj["memories"][memory_id]
            proj["meta"]["updated_at"] = _now_iso()
            self._save()
            return True
        return False

    def search_memories(self, project_id: str, query: str, top_k: int = 5) -> List[ProjectMemory]:
        all_mems = self.get_memories(project_id)
        if not all_mems or not query.strip():
            return all_mems[:top_k]

        q_terms = set(query.lower().split())
        scored = []

        for m in all_mems:
            text = f"{m.key} {m.memory_type} {m.source_agent} {json.dumps(m.value)}".lower()
            matches = sum(1 for term in q_terms if term in text)
            # Boost score based on importance
            imp_boost = {"CRITICAL": 3.0, "HIGH": 2.0, "MEDIUM": 1.0, "LOW": 0.5}.get(m.importance, 1.0)
            score = matches * imp_boost
            scored.append((score, m))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]

    def summarize_memories(self, project_id: str, max_items: int = 30) -> int:
        """
        If memory count exceeds max_items, condenses older LOW/MEDIUM items
        while preserving HIGH/CRITICAL items. Returns count of purged memories.
        """
        proj = self.data.get(project_id)
        if not proj:
            return 0

        memories = proj.get("memories", {})
        if len(memories) <= max_items:
            return 0

        items = list(memories.values())
        items.sort(key=lambda x: x.get("updated_at", ""))

        # Identify items to prune: LOW or MEDIUM importance, starting from oldest
        purged = 0
        for item in items:
            if len(proj["memories"]) <= max_items:
                break
            if item.get("importance") in (ImportanceLevel.LOW.value, ImportanceLevel.MEDIUM.value):
                del proj["memories"][item["id"]]
                purged += 1

        if purged > 0:
            proj["meta"]["updated_at"] = _now_iso()
            self._save()
            logger.info(f"Summarized/pruned {purged} older memories for project '{project_id}'")

        return purged


# Global LongTermMemory instance
global_long_term_memory = LongTermMemory()
