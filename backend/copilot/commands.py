"""
AIForge Day 23 — Copilot Command Palette Handler
=================================================
Handles quick slash commands (/explain, /search, /test, /debug, /security, /performance, /impact, /whatif, /deploy, /rollback, /incidents, /memory, /architecture).
"""

import logging
from typing import Dict, Any, Tuple, Optional

from backend.copilot.models import CopilotIntent

_logger = logging.getLogger("aiforge.copilot.commands")


class CommandPaletteHandler:
    """
    Parses quick slash commands and maps them to CopilotIntents.
    """

    COMMAND_MAP: Dict[str, CopilotIntent] = {
        "/explain": CopilotIntent.EXPLANATION,
        "/search": CopilotIntent.SEARCH,
        "/test": CopilotIntent.TESTING,
        "/debug": CopilotIntent.DEBUGGING,
        "/security": CopilotIntent.SECURITY,
        "/performance": CopilotIntent.PERFORMANCE,
        "/impact": CopilotIntent.ANALYSIS,
        "/whatif": CopilotIntent.WHAT_IF,
        "/deploy": CopilotIntent.DEPLOYMENT,
        "/rollback": CopilotIntent.DEPLOYMENT,
        "/incidents": CopilotIntent.INCIDENT,
        "/memory": CopilotIntent.QUESTION,
        "/architecture": CopilotIntent.ARCHITECTURE,
    }

    def parse_command(self, raw_input: str) -> Tuple[bool, Optional[str], Optional[CopilotIntent], str]:
        stripped = raw_input.strip()
        if not stripped.startswith("/"):
            return False, None, None, raw_input

        parts = stripped.split(" ", 1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        intent = self.COMMAND_MAP.get(cmd)
        if intent:
            return True, cmd, intent, arg or f"Execute {cmd}"

        return False, None, None, raw_input


global_command_palette_handler = CommandPaletteHandler()
