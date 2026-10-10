"""
AIForge Day 23 — Copilot Permissions & Safety Policy Engine
=============================================================
Classifies request action levels (READ_ONLY, SAFE_ACTION, MUTATING_ACTION, HIGH_RISK_ACTION),
enforces project isolation, and applies Prompt Guard injection scanning on untrusted inputs.
"""

import logging
from typing import Dict, Any, Tuple

from backend.copilot.models import CopilotIntent, ActionCategory
from backend.security.prompt_guard import global_prompt_guard

_logger = logging.getLogger("aiforge.copilot.permissions")


class CopilotPermissionsEngine:
    """
    Enforces action categorization, permission checks, and prompt safety.
    """

    def classify_action_category(self, intent: CopilotIntent, user_prompt: str) -> ActionCategory:
        p_lower = user_prompt.lower()

        if "deploy" in p_lower or "rollback" in p_lower or intent == CopilotIntent.DEPLOYMENT:
            return ActionCategory.HIGH_RISK_ACTION

        if intent in (CopilotIntent.MODIFICATION, CopilotIntent.DEBUGGING) or "fix" in p_lower or "modify" in p_lower or "add" in p_lower:
            return ActionCategory.MUTATING_ACTION

        if intent in (CopilotIntent.TESTING, CopilotIntent.SECURITY, CopilotIntent.PERFORMANCE) or "run" in p_lower or "scan" in p_lower or "benchmark" in p_lower:
            return ActionCategory.SAFE_ACTION

        return ActionCategory.READ_ONLY

    def validate_request_safety(self, project_id: str, user_prompt: str) -> Tuple[bool, str]:
        # Prompt injection protection
        guard_res = global_prompt_guard.validate_content(user_prompt, source="user_prompt")
        if guard_res.risk in ("HIGH", "MEDIUM"):
            _logger.warning(f"[CopilotPermissions] Blocked prompt injection in '{project_id}': {guard_res.reason}")
            return False, f"Request blocked by Prompt Guard: {guard_res.reason}"

        return True, "Safe"


global_copilot_permissions_engine = CopilotPermissionsEngine()
