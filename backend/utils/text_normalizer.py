"""
AIForge Text Normalizer Utility
===============================
Provides text normalization functions for user prompts.
Normalizes prompts for classification while keeping original prompts untouched for downstream agent execution.
"""

import re


def normalize_prompt(prompt: str) -> str:
    """
    Normalizes a user prompt for intent classification.
    - Strips leading/trailing whitespace.
    - Standardizes internal whitespace (collapses multiple spaces/newlines unless in code).
    - Converts to lowercase for rule matching.
    - Keeps original prompt intact for agent execution.
    """
    if not prompt:
        return ""

    # Strip surrounding whitespace
    cleaned = prompt.strip()

    # If prompt contains code block fenced with ```, preserve code block and normalize surrounding text
    if "```" in cleaned:
        parts = cleaned.split("```")
        for i in range(0, len(parts), 2):
            parts[i] = re.sub(r'\s+', ' ', parts[i]).strip().lower()
        return "```".join(parts)

    # Collapse multiple whitespace characters into single space and lowercase
    normalized = re.sub(r'\s+', ' ', cleaned).strip().lower()
    return normalized.rstrip('.!?')
