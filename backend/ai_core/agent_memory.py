"""
AIForge Next-Gen AI Agent Core — Modular Memory Architecture
=============================================================
Supports:
- Short-Term Memory (Session / active context)
- Long-Term Memory (Persistent user preferences & architectural constraints)
- Task Memory (Ephemeral execution graph state)
- Semantic Memory (Relevance scoring & tenant isolation)
"""

import time
import uuid
import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from pathlib import Path

_logger = logging.getLogger("aiforge.ai_core.memory")


class MemoryType(str):
    SHORT_TERM = "SHORT_TERM"
    LONG_TERM = "LONG_TERM"
    TASK = "TASK"
    SEMANTIC = "SEMANTIC"


class MemoryRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"mem_{uuid.uuid4().hex[:8]}")
    user_id: str
    project_id: Optional[str] = None
    memory_type: str = "LONG_TERM"  # SHORT_TERM, LONG_TERM, TASK, SEMANTIC
    key: str
    content: str
    relevance_score: float = 1.0
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


class AgentMemoryManager:
    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            self.storage_dir = Path(__file__).resolve().parent.parent / "data" / "agent_memory"

        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_file = self.storage_dir / "memories.json"
        self._memories: Dict[str, MemoryRecord] = {}
        self._load()

    def _load(self):
        if not self.storage_file.exists():
            return
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    if not item.get("user_id") or item.get("user_id") == "user_default":
                        continue          # demo records from earlier versions belong to nobody
                    m = MemoryRecord(**item)
                    self._memories[m.id] = m
        except Exception as e:
            _logger.error(f"Error loading agent memories: {e}")

    def _save(self):
        try:
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump([m.model_dump() for m in self._memories.values()], f, indent=2)
        except Exception as e:
            _logger.error(f"Error saving agent memories: {e}")

    def store(self, key: str, content: str, user_id: str, memory_type: str = "LONG_TERM", project_id: Optional[str] = None) -> MemoryRecord:
        record = MemoryRecord(
            user_id=user_id,
            project_id=project_id,
            memory_type=memory_type,
            key=key.strip(),
            content=content.strip(),
            relevance_score=1.0
        )
        self._memories[record.id] = record
        self._save()
        return record

    def search(self, query: str, user_id: str, project_id: Optional[str] = None, limit: int = 5) -> List[MemoryRecord]:
        q_lower = query.lower()
        results = []
        for m in self._memories.values():
            if m.user_id != user_id:
                continue
            if project_id and m.project_id and m.project_id != project_id:
                continue
            
            # Simple keyword scoring
            score = 0.0
            if q_lower in m.key.lower():
                score += 0.5
            if q_lower in m.content.lower():
                score += 0.4
            words = q_lower.split()
            matching_words = sum(1 for w in words if w in m.content.lower())
            if words:
                score += (matching_words / len(words)) * 0.4

            if score > 0.1 or not query:
                rec_copy = m.model_copy()
                rec_copy.relevance_score = min(1.0, round(score if score > 0 else 0.85, 2))
                results.append(rec_copy)

        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:limit]

    def list_memories(self, user_id: str) -> List[MemoryRecord]:
        return [m for m in self._memories.values() if m.user_id == user_id]

    def delete_memory(self, memory_id: str, user_id: str) -> bool:
        if memory_id in self._memories and self._memories[memory_id].user_id == user_id:
            del self._memories[memory_id]
            self._save()
            return True
        return False


global_memory_manager = AgentMemoryManager()
