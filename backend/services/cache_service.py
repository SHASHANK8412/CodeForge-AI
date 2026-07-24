"""
AIForge Node-Level Caching Service
==================================
Hashes inputs (prompt, prior node JSON contracts) for each node (Planner, Architect, Frontend, Backend, Database, etc.)
and caches generated outputs to accelerate redundant pipeline runs.
"""

import json
import hashlib
import logging
from typing import Dict, Any, Optional

_logger = logging.getLogger("aiforge.cache")


class NodeCacheService:
    """
    Node-level caching service for LangGraph workflow execution.
    """

    def __init__(self) -> None:
        self._cache: Dict[str, Any] = {}

    def _generate_key(self, node_name: str, input_data: Any) -> str:
        serialized = json.dumps(input_data, sort_keys=True, default=str)
        hash_digest = hashlib.sha256(f"{node_name}:{serialized}".encode("utf-8")).hexdigest()
        return f"{node_name}:{hash_digest[:16]}"

    def get(self, node_name: str, input_data: Any) -> Optional[Any]:
        key = self._generate_key(node_name, input_data)
        if key in self._cache:
            _logger.info(f"NodeCacheService: HIT for node '{node_name}' (key: {key})")
            return self._cache[key]
        _logger.debug(f"NodeCacheService: MISS for node '{node_name}'")
        return None

    def set(self, node_name: str, input_data: Any, output_data: Any) -> None:
        key = self._generate_key(node_name, input_data)
        self._cache[key] = output_data
        _logger.info(f"NodeCacheService: STORED cached output for node '{node_name}' (key: {key})")

    def clear(self) -> None:
        self._cache.clear()
        _logger.info("NodeCacheService: Cache cleared")


global_cache_service = NodeCacheService()
