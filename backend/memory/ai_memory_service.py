"""
AIForge Next Generation AI Memory Service
==========================================
Persistent, Isolated & Smart-Recall Memory Engine for:
1. Personal Memory (User preferences, preferred tech stack, coding/writing style, custom instructions)
2. Project Memory (Isolated per-project architecture decisions, tasks, requirements, constraints, docs)
3. Smart Recall (Relevance-based semantic & keyword scoring, scope prioritization, contextual prompt builder)
4. Memory Controls (Remember, Forget, Edit, Clear Project, Clear All, Pinned state)
5. Automatic Memory Suggestion Engine (Detects actionable facts, preferences, and decisions from chat turns)
"""

import os
import json
import time
import uuid
import re
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field
from pathlib import Path

_logger = logging.getLogger("aiforge.memory.ai_memory_service")


class MemoryScope(str, Enum):
    PERSONAL = "PERSONAL"
    PROJECT = "PROJECT"


class MemoryCategory(str, Enum):
    PREFERENCES = "Preferences"
    TECH_STACK = "Tech Stack"
    ARCHITECTURE = "Architecture"
    REQUIREMENTS = "Requirements"
    CONVERSATION = "Conversation"
    TASKS = "Tasks"
    RULES = "Rules & Constraints"


class MemoryImportance(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AIMemoryItem(BaseModel):
    id: str = Field(default_factory=lambda: f"mem_{uuid.uuid4().hex[:10]}")
    user_id: str = "default_user"
    scope: MemoryScope = MemoryScope.PERSONAL
    project_id: Optional[str] = None  # None for Personal, string for Project-specific
    category: MemoryCategory = MemoryCategory.PREFERENCES
    title: str
    content: str
    importance: MemoryImportance = MemoryImportance.HIGH
    source: str = "User"  # User, Conversation, Agent, Architecture Decision
    tags: List[str] = Field(default_factory=list)
    pinned: bool = False
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    updated_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    last_used_at: Optional[str] = None
    usage_count: int = 0


DEFAULT_INITIAL_MEMORIES = [
    {
        "id": "mem-pers-1",
        "user_id": "default_user",
        "scope": "PERSONAL",
        "project_id": None,
        "category": "Tech Stack",
        "title": "Preferred Full-Stack Architecture",
        "content": "User prefers React with Tailwind CSS on frontend, and FastAPI with PostgreSQL & SQLAlchemy on backend.",
        "importance": "CRITICAL",
        "source": "User",
        "tags": ["FastAPI", "React", "Tailwind", "PostgreSQL"],
        "pinned": True,
        "created_at": "2026-08-20 10:00:00",
        "updated_at": "2026-08-20 10:00:00",
        "last_used_at": "Just now",
        "usage_count": 18
    },
    {
        "id": "mem-pers-2",
        "user_id": "default_user",
        "scope": "PERSONAL",
        "project_id": None,
        "category": "Preferences",
        "title": "Coding & Design Conventions",
        "content": "Always write clean, modular functional React code with strict PropTypes/TypeScript, async/await for async operations, and meaningful error handling.",
        "importance": "HIGH",
        "source": "User",
        "tags": ["Conventions", "Code Quality", "Clean Code"],
        "pinned": True,
        "created_at": "2026-08-21 11:30:00",
        "updated_at": "2026-08-21 11:30:00",
        "last_used_at": "1 hour ago",
        "usage_count": 12
    },
    {
        "id": "mem-proj-1",
        "user_id": "default_user",
        "scope": "PROJECT",
        "project_id": "aiforge-fooddelivery-ai",
        "category": "Architecture",
        "title": "FoodDelivery AI JWT & Role-Based Access",
        "content": "Authentication uses RS256 JWT tokens with Customer, Restaurant Owner, and Courier roles. Tokens expire in 60 minutes with auto-refresh.",
        "importance": "HIGH",
        "source": "Architecture Decision",
        "tags": ["Auth", "JWT", "RBAC", "FoodDelivery"],
        "pinned": False,
        "created_at": "2026-08-25 14:15:00",
        "updated_at": "2026-08-25 14:15:00",
        "last_used_at": "2 hours ago",
        "usage_count": 9
    },
    {
        "id": "mem-proj-2",
        "user_id": "default_user",
        "scope": "PROJECT",
        "project_id": "aiforge-fooddelivery-ai",
        "category": "Tasks",
        "title": "Stripe Webhook & Order Dispatch State Machine",
        "content": "Order status transitions: PENDING -> PAID -> KITCHEN_PREPARING -> READY_FOR_PICKUP -> OUT_FOR_DELIVERY -> DELIVERED. Webhooks handle payment intents.",
        "importance": "HIGH",
        "source": "Conversation",
        "tags": ["Stripe", "Orders", "State Machine"],
        "pinned": False,
        "created_at": "2026-08-28 16:45:00",
        "updated_at": "2026-08-28 16:45:00",
        "last_used_at": "Yesterday",
        "usage_count": 5
    }
]


class AIMemoryService:
    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            self.storage_dir = Path(__file__).resolve().parent.parent / "data" / "memory"
        
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_file = self.storage_dir / "ai_memories.json"
        self._memories: Dict[str, AIMemoryItem] = {}
        self._load()

    def _load(self):
        try:
            if self.storage_file.exists():
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item_dict in data:
                        item = AIMemoryItem(**item_dict)
                        self._memories[item.id] = item
            else:
                # Initialize with rich defaults
                for item_dict in DEFAULT_INITIAL_MEMORIES:
                    item = AIMemoryItem(**item_dict)
                    self._memories[item.id] = item
                self._save()
        except Exception as e:
            _logger.error(f"Error loading AI memories: {e}")
            for item_dict in DEFAULT_INITIAL_MEMORIES:
                item = AIMemoryItem(**item_dict)
                self._memories[item.id] = item

    def _save(self):
        try:
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump([m.model_dump() for m in self._memories.values()], f, indent=2)
        except Exception as e:
            _logger.error(f"Error saving AI memories: {e}")

    def list_memories(
        self,
        scope: Optional[str] = None,
        project_id: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "recent"  # recent, most_used, importance, title
    ) -> List[AIMemoryItem]:
        items = list(self._memories.values())

        if scope:
            items = [m for m in items if m.scope.value.upper() == scope.upper()]

        if project_id:
            items = [m for m in items if m.project_id == project_id]

        if category and category != "All":
            items = [m for m in items if m.category.value.lower() == category.lower()]

        if search:
            q = search.lower().strip()
            items = [
                m for m in items
                if q in m.title.lower()
                or q in m.content.lower()
                or any(q in t.lower() for t in m.tags)
            ]

        # Sorting
        if sort_by == "most_used":
            items.sort(key=lambda m: (m.pinned, m.usage_count), reverse=True)
        elif sort_by == "importance":
            importance_weight = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
            items.sort(key=lambda m: (m.pinned, importance_weight.get(m.importance.value, 0)), reverse=True)
        elif sort_by == "title":
            items.sort(key=lambda m: m.title.lower())
        else:  # recent
            items.sort(key=lambda m: (m.pinned, m.updated_at), reverse=True)

        return items

    def get_memory(self, memory_id: str) -> Optional[AIMemoryItem]:
        return self._memories.get(memory_id)

    def create_memory(
        self,
        title: str,
        content: str,
        scope: MemoryScope = MemoryScope.PERSONAL,
        project_id: Optional[str] = None,
        category: MemoryCategory = MemoryCategory.PREFERENCES,
        importance: MemoryImportance = MemoryImportance.HIGH,
        source: str = "User",
        tags: Optional[List[str]] = None,
        pinned: bool = False,
        user_id: str = "default_user"
    ) -> AIMemoryItem:
        item = AIMemoryItem(
            user_id=user_id,
            scope=scope,
            project_id=project_id if scope == MemoryScope.PROJECT else None,
            category=category,
            title=title.strip(),
            content=content.strip(),
            importance=importance,
            source=source,
            tags=tags or [],
            pinned=pinned,
            created_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            updated_at=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        self._memories[item.id] = item
        self._save()
        _logger.info(f"Created memory '{item.title}' [{item.scope.value}]")
        return item

    def update_memory(
        self,
        memory_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[MemoryCategory] = None,
        importance: Optional[MemoryImportance] = None,
        tags: Optional[List[str]] = None,
        pinned: Optional[bool] = None,
        project_id: Optional[str] = None
    ) -> Optional[AIMemoryItem]:
        item = self._memories.get(memory_id)
        if not item:
            return None

        if title is not None:
            item.title = title.strip()
        if content is not None:
            item.content = content.strip()
        if category is not None:
            item.category = category
        if importance is not None:
            item.importance = importance
        if tags is not None:
            item.tags = tags
        if pinned is not None:
            item.pinned = pinned
        if project_id is not None:
            item.project_id = project_id

        item.updated_at = time.strftime("%Y-%m-%d %H:%M:%S")
        self._save()
        return item

    def delete_memory(self, memory_id: str) -> bool:
        if memory_id in self._memories:
            del self._memories[memory_id]
            self._save()
            return True
        return False

    def clear_project_memory(self, project_id: str) -> int:
        to_delete = [m_id for m_id, m in self._memories.items() if m.project_id == project_id]
        for m_id in to_delete:
            del self._memories[m_id]
        if to_delete:
            self._save()
        return len(to_delete)

    def clear_all_memory(self) -> int:
        count = len(self._memories)
        self._memories.clear()
        self._save()
        return count

    def smart_recall(
        self,
        user_prompt: str,
        project_id: Optional[str] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Smart Recall: Identifies and retrieves only relevant memories for a given user prompt.
        Prioritizes project-specific context over general personal preferences.
        """
        prompt_lower = user_prompt.lower()
        words = set(re.findall(r"\b\w{3,}\b", prompt_lower))

        scored_items: List[tuple[float, AIMemoryItem]] = []

        importance_boost = {
            MemoryImportance.CRITICAL: 2.0,
            MemoryImportance.HIGH: 1.5,
            MemoryImportance.MEDIUM: 1.0,
            MemoryImportance.LOW: 0.7
        }

        for item in self._memories.values():
            score = 0.0

            # Title matches
            title_lower = item.title.lower()
            if any(w in title_lower for w in words):
                score += 3.0

            # Content matches
            content_lower = item.content.lower()
            matched_words = [w for w in words if w in content_lower]
            score += len(matched_words) * 1.2

            # Tag matches
            for tag in item.tags:
                if tag.lower() in prompt_lower:
                    score += 2.5

            # Scope prioritization: project matches get strong boost when in project context
            if project_id and item.project_id == project_id:
                score += 2.0
            elif item.scope == MemoryScope.PERSONAL:
                # Personal memories with pinned status always get a base presence
                if item.pinned:
                    score += 1.0

            # Importance multiplier
            score *= importance_boost.get(item.importance, 1.0)

            # Pinned items boost
            if item.pinned:
                score += 1.5

            if score > 0.5:
                scored_items.append((score, item))

        scored_items.sort(key=lambda x: x[0], reverse=True)
        top_items = [item for score, item in scored_items[:limit]]

        # If few items matched but user has pinned personal tech stack/preferences, include them
        if len(top_items) < limit:
            for item in self._memories.values():
                if item.pinned and item not in top_items:
                    top_items.append(item)
                    if len(top_items) >= limit:
                        break

        # Record usage
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        for item in top_items:
            item.usage_count += 1
            item.last_used_at = now_str
        if top_items:
            self._save()

        # Build prompt-ready context string
        context_parts = []
        if top_items:
            context_parts.append("### Active AI Memory Context:")
            for item in top_items:
                scope_label = f"Project: {item.project_id}" if item.project_id else "Personal Preference"
                context_parts.append(f"- **[{scope_label}] {item.title}**: {item.content}")

        return {
            "recalled_memories": [item.model_dump() for item in top_items],
            "context_prompt": "\n".join(context_parts),
            "total_recalled": len(top_items),
            "memory_active": len(top_items) > 0
        }

    def generate_memory_suggestions(self, user_prompt: str, assistant_response: str) -> List[Dict[str, Any]]:
        """
        Analyzes conversation turn and proposes actionable memories if user expresses explicit preferences or decisions.
        """
        suggestions = []
        combined_text = f"{user_prompt}\n{assistant_response}"

        # Detect explicit preference patterns
        pref_match = re.search(r"(?:i prefer|always use|make sure to use|stick with|our standard is)\s+([^.\n]+)", user_prompt, re.I)
        if pref_match:
            cand = pref_match.group(1).strip()
            suggestions.append({
                "title": f"Preference: {cand[:40]}",
                "content": f"User preference: {cand}",
                "category": MemoryCategory.PREFERENCES.value,
                "scope": MemoryScope.PERSONAL.value,
                "importance": MemoryImportance.HIGH.value,
                "tags": ["Preference", "User Defined"]
            })

        # Detect architecture decision patterns
        decision_match = re.search(r"(?:we decided on|let's choose|selected|architected with)\s+([^.\n]+)", combined_text, re.I)
        if decision_match and not suggestions:
            dec = decision_match.group(1).strip()
            suggestions.append({
                "title": f"Architecture Decision: {dec[:40]}",
                "content": f"Agreed architecture: {dec}",
                "category": MemoryCategory.ARCHITECTURE.value,
                "scope": MemoryScope.PROJECT.value,
                "importance": MemoryImportance.HIGH.value,
                "tags": ["Architecture", "Decision"]
            })

        return suggestions


global_ai_memory_service = AIMemoryService()
