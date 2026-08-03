"""
AIForge Repository Task Analyzer
================================
Classifies user intent and target scope into a RepositoryTask (READ_ONLY vs MODIFY).
"""

import re
import logging
from typing import List, Dict, Any, Optional

from backend.repository.models import RepositoryTask

_logger = logging.getLogger("aiforge.repository.task_analyzer")


class RepositoryTaskAnalyzer:
    """
    Analyzes user query to extract task mode, target features, and symbols.
    """

    READ_ONLY_KEYWORDS = ["explain", "how does", "where is", "find", "what is", "search", "show me", "analyze architecture"]
    MODIFY_KEYWORDS = ["add", "implement", "fix", "update", "modify", "refactor", "create", "delete", "rewrite"]

    def analyze_task(self, user_prompt: str, intent: str = "CODING") -> RepositoryTask:
        prompt_clean = user_prompt.lower().strip()

        # Determine task mode
        mode = "MODIFY"
        if any(prompt_clean.startswith(kw) for kw in self.READ_ONLY_KEYWORDS) and not any(kw in prompt_clean for kw in ["and fix", "and add", "and modify"]):
            mode = "READ_ONLY"

        if intent in ["GENERAL_QA", "EXPLANATION", "RAG_QUERY", "RESUME"]:
            mode = "READ_ONLY"

        # Extract features and keywords
        target_features = []
        if "jwt" in prompt_clean or "auth" in prompt_clean or "login" in prompt_clean:
            target_features.append("authentication")
        if "user" in prompt_clean or "profile" in prompt_clean:
            target_features.append("user_management")
        if "test" in prompt_clean:
            target_features.append("testing")

        target_symbols = []
        words = re.findall(r"\b[A-Za-z0-9_]{3,}\b", user_prompt)
        for w in words:
            if any(char.isupper() for char in w) or "_" in w:
                target_symbols.append(w)

        layers = []
        if any(k in prompt_clean for k in ["route", "endpoint", "api", "url"]):
            layers.append("route")
        if any(k in prompt_clean for k in ["service", "logic", "manager"]):
            layers.append("service")
        if any(k in prompt_clean for k in ["model", "schema", "database", "table"]):
            layers.append("model")
        if "test" in prompt_clean:
            layers.append("test")

        return RepositoryTask(
            task_type=mode,
            target_features=target_features,
            target_symbols=target_symbols,
            keywords=words[:10],
            likely_layers=layers or ["route", "service", "model"]
        )


global_repository_task_analyzer = RepositoryTaskAnalyzer()
