import logging
from typing import Dict, Any

logger = logging.getLogger("aiforge.models.capabilities")


class CapabilityScores:
    """
    CapabilityScores stores task rating matrices for LLMs across:
    coding, reasoning, architecture, planning, security, and documentation.
    """

    DEFAULT_CAPABILITIES: Dict[str, Dict[str, int]] = {
        "qwen2.5-coder": {
            "planning": 8,
            "architecture": 8,
            "backend": 10,
            "frontend": 10,
            "database": 8,
            "documentation": 8,
            "testing": 9,
            "security": 8,
            "speed": 9
        },
        "deepseek-coder": {
            "planning": 8,
            "architecture": 10,
            "backend": 9,
            "frontend": 8,
            "database": 10,
            "documentation": 8,
            "testing": 9,
            "security": 10,
            "speed": 8
        },
        "llama3.1": {
            "planning": 10,
            "architecture": 9,
            "backend": 7,
            "frontend": 7,
            "database": 8,
            "documentation": 10,
            "testing": 8,
            "security": 8,
            "speed": 8
        },
        "mistral-7b": {
            "planning": 8,
            "architecture": 8,
            "backend": 8,
            "frontend": 8,
            "database": 7,
            "documentation": 9,
            "testing": 8,
            "security": 7,
            "speed": 9
        }
    }


# Global CapabilityScores Instance
global_capability_scores = CapabilityScores()
