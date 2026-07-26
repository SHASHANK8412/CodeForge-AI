import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("aiforge.memory.short_term")


class ShortTermMemory:
    """
    ShortTermMemory holds transient workflow state for the active project generation task.
    Lifespan: Single execution session.
    """

    def __init__(self):
        self._store: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)

    def get_all(self) -> Dict[str, Any]:
        return dict(self._store)

    def clear(self) -> None:
        self._store.clear()


# Global ShortTermMemory instance
global_short_term_memory = ShortTermMemory()
