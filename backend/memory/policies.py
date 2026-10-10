"""
AIForge Day 22 — Memory Security & Privacy Policy Engine
========================================================
Enforces strict secret protection (redacting API keys, passwords, database credentials),
project isolation, and visibility access controls (USER_VISIBLE vs AGENT_ONLY vs SYSTEM).
"""

import re
import logging
from typing import Dict, Any, Tuple

from backend.memory.models import EngineeringMemory, MemoryVisibility

_logger = logging.getLogger("aiforge.memory.policies")


class MemorySecurityPolicyEngine:
    """
    Enforces memory safety, secret masking, and project isolation.
    """

    def sanitize_memory_content(self, text: str) -> Tuple[bool, str]:
        pattern = r"(?i)(key|secret|password|token|bearer|jwt|database_url|url)\s*=\s*['\"]?([^\s'\"]+)['\"]?"
        clean_text = re.sub(pattern, r"\1=****", text)
        clean_text = re.sub(r"://([^:@]+):([^@]+)@", r"://\1:****@", clean_text)
        has_secrets = clean_text != text
        if has_secrets:
            _logger.warning("[MemorySecurity] Redacted hardcoded secret from memory payload")

        return has_secrets, clean_text

    def validate_project_access(self, memory: EngineeringMemory, target_project_id: str) -> bool:
        return memory.project_id == target_project_id

    def filter_user_visible(self, memories: list[EngineeringMemory]) -> list[EngineeringMemory]:
        return [m for m in memories if m.visibility in (MemoryVisibility.USER_VISIBLE, MemoryVisibility.AGENT_ONLY)]


global_memory_security_policy = MemorySecurityPolicyEngine()
