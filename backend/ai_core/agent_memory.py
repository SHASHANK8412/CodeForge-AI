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
    user_id: str = "user_default"
    project_id: Optional[str] = "aiforge-fooddelivery-ai"
    memory_type: str = "LONG_TERM"  # SHORT_TERM, LONG_TERM, TASK, SEMANTIC
    key: str
    content: str
    relevance_score: float = 1.0
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


INITIAL_MEMORIES = [
    {
        "id": "mem_pref_ts",
        "user_id": "user_default",
        "project_id": "aiforge-fooddelivery-ai",
        "memory_type": "LONG_TERM",
        "key": "frontend_tech_stack",
        "content": "User prefers React with Tailwind CSS and strict TypeScript types over JavaScript.",
        "relevance_score": 0.96
    },
    {
        "id": "mem_arch_redis",
        "user_id": "user_default",
        "project_id": "aiforge-fooddelivery-ai",
        "memory_type": "SEMANTIC",
        "key": "geolocation_streaming",
        "content": "Architecture decision: Courier real-time location stream uses Redis Streams with consumer groups for 50ms broadcast latency.",
        "relevance_score": 0.94
    },
    {
        "id": "mem_sec_jwt",
        "user_id": "user_default",
        "project_id": "aiforge-fooddelivery-ai",
        "memory_type": "LONG_TERM",
        "key": "security_policy",
        "content": "All API endpoints require asymmetric RS256 JWT tokens and rate-limiting bucket middleware.",
        "relevance_score": 0.98
    }
]


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
        try:
            if self.storage_file.exists():
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        m = MemoryRecord(**item)
                        self._memories[m.id] = m
            else:
                for item in INITIAL_MEMORIES:
                    m = MemoryRecord(**item)
                    self._memories[m.id] = m
                self._save()
        except Exception as e:
            _logger.error(f"Error loading agent memories: {e}")
            for item in INITIAL_MEMORIES:
                m = MemoryRecord(**item)
                self._memories[m.id] = m

    def _save(self):
        try:
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump([m.model_dump() for m in self._memories.values()], f, indent=2)
        except Exception as e:
            _logger.error(f"Error saving agent memories: {e}")

    def store(self, key: str, content: str, memory_type: str = "LONG_TERM", project_id: Optional[str] = None, user_id: str = "user_default") -> MemoryRecord:
        record = MemoryRecord(
            user_id=user_id,
            project_id=project_id or "aiforge-fooddelivery-ai",
            memory_type=memory_type,
            key=key.strip(),
            content=content.strip(),
            relevance_score=1.0
        )
        self._memories[record.id] = record
        self._save()
        return record

    def search(self, query: str, user_id: str = "user_default", project_id: Optional[str] = None, limit: int = 5) -> List[MemoryRecord]:
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

    def list_memories(self, user_id: str = "user_default") -> List[MemoryRecord]:
        return [m for m in self._memories.values() if m.user_id == user_id]

    def delete_memory(self, memory_id: str) -> bool:
        if memory_id in self._memories:
            del self._memories[memory_id]
            self._save()
            return True
        return False


global_memory_manager = AgentMemoryManager()
