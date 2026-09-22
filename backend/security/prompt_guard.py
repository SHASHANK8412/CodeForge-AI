"""
AIForge V2 — Prompt Injection Defense Engine (PromptGuard)
==========================================================
Scans retrieved RAG documents and user prompts for adversarial injection attempts
(e.g., "ignore previous instructions", "reveal system prompt", "bypass security").
"""

import re
import logging
from typing import List

from backend.security.models import PromptGuardResult

_logger = logging.getLogger("aiforge.security.prompt_guard")

INJECTION_PATTERNS = [
    (r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions", "Instruction override attempt"),
    (r"(?i)reveal\s+(the\s+)?system\s+prompt", "System prompt exfiltration attempt"),
    (r"(?i)expose\s+(all\s+)?credentials|passwords|secrets", "Credential harvest attempt"),
    (r"(?i)bypass\s+(authentication|security|authorization)", "Security control bypass attempt"),
    (r"(?i)execute\s+arbitrary\s+commands", "Arbitrary command execution attempt"),
    (r"(?i)disable\s+(auth|security|validation)", "Security disablement attempt"),
]


class PromptGuard:
    """
    Evaluates risk of prompt injection in user input or retrieved RAG documents.
    """

    def validate_content(self, content: str, source: str = "document") -> PromptGuardResult:
        if not content:
            return PromptGuardResult(risk="LOW", source=source, reason="Empty content")

        flagged: List[str] = []
        reasons: List[str] = []

        for pattern, reason in INJECTION_PATTERNS:
            match = re.search(pattern, content)
            if match:
                flagged.append(match.group(0))
                reasons.append(reason)

        if len(flagged) >= 2:
            return PromptGuardResult(
                risk="HIGH",
                source=source,
                reason=f"Document attempts to override agent instructions: {'; '.join(reasons)}",
                flagged_terms=flagged
            )
        elif len(flagged) == 1:
            return PromptGuardResult(
                risk="MEDIUM",
                source=source,
                reason=f"Potential injection phrase detected: {reasons[0]}",
                flagged_terms=flagged
            )
        else:
            return PromptGuardResult(
                risk="LOW",
                source=source,
                reason="No prompt injection patterns detected."
            )


global_prompt_guard = PromptGuard()
