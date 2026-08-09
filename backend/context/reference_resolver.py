"""
AIForge Reference Resolver
==========================
Resolves contextual references ("it", "that", "the code", "the error", "the algorithm")
to recent entities and conversation topics, producing a resolved prompt for Intent Classifier.
"""

import re
from typing import Dict, Any, List, Tuple
from backend.context.models import ConversationMessage


class ReferenceResolver:
    """
    Resolves ambiguous references using recent conversation history.
    """

    REFERENCE_MAP = {
        "it": "the previous algorithm or concept",
        "that": "the previous topic",
        "this": "the current implementation",
        "the code": "the previously generated code solution",
        "the error": "the reported traceback error",
        "the function": "the previously discussed function",
        "the database": "the selected database system",
        "the document": "the uploaded document file",
        "the resume": "the analyzed resume text",
        "qualifying": "Formula 1 qualifying",
        "tyres": "Formula 1 tyres",
        "tires": "Formula 1 tires"
    }

    def _extract_recent_subject(self, messages: List[ConversationMessage]) -> str:
        """Extracts the primary subject from recent user/assistant turns."""
        for msg in reversed(messages):
            content = msg.content.strip()
            # Check for algorithm names
            for algo in ["binary search", "merge sort", "quicksort", "bfs", "dfs", "lru cache", "linked list", "stack", "queue"]:
                if algo in content.lower():
                    return algo

            # Check for topic headers
            if "formula 1" in content.lower():
                return "Formula 1"
            if "docker" in content.lower():
                return "Docker"
            if "fastapi" in content.lower():
                return "FastAPI"
            if "react" in content.lower():
                return "React"

        return ""

    def resolve(
        self,
        user_prompt: str,
        recent_messages: List[ConversationMessage],
        current_topic: str = ""
    ) -> Tuple[str, Dict[str, str]]:
        if not recent_messages:
            return user_prompt, {}

        resolved_prompt = user_prompt
        resolved_refs: Dict[str, str] = {}

        last_user_msg = next((m for m in reversed(recent_messages) if m.role == "user"), None)
        last_assistant_msg = next((m for m in reversed(recent_messages) if m.role == "assistant"), None)

        subject = current_topic or self._extract_recent_subject(recent_messages)

        prompt_lower = user_prompt.strip().lower()

        # 1. Handle "Make it <Language>" pattern
        match_make_it = re.search(r"\bmake it\s+([a-zA-Z\+#]+)", prompt_lower)
        if match_make_it:
            target_lang = match_make_it.group(1).title()
            if subject:
                resolved_prompt = f"Implement {subject} in {target_lang}"
                resolved_refs["it"] = f"{subject} in {target_lang}"
            elif last_user_msg:
                resolved_prompt = f"{last_user_msg.content} in {target_lang}"
                resolved_refs["it"] = f"previous code in {target_lang}"

        # 2. Handle "Explain qualifying" / "What about tyres" under Formula 1 topic
        elif subject.lower() in ["formula 1", "f1"] and ("qualifying" in prompt_lower or "tyres" in prompt_lower or "tires" in prompt_lower):
            if "qualifying" in prompt_lower:
                resolved_prompt = "Explain Formula 1 qualifying process"
                resolved_refs["qualifying"] = "Formula 1 qualifying"
            elif "tyres" in prompt_lower or "tires" in prompt_lower:
                resolved_prompt = "Explain Formula 1 tyre strategy"
                resolved_refs["tyres"] = "Formula 1 tyres"

        # 3. Handle "Implement it in Python" / "Explain it"
        elif "it" in prompt_lower.split() or "that" in prompt_lower.split():
            if subject:
                if "implement" in prompt_lower or "write" in prompt_lower or "code" in prompt_lower:
                    resolved_prompt = f"Implement {subject} in Python"
                    resolved_refs["it"] = subject
                elif "explain" in prompt_lower:
                    resolved_prompt = f"Explain {subject}"
                    resolved_refs["it"] = subject

        # 4. Handle "Why?" / "Explain that more simply"
        elif prompt_lower in ["why?", "why", "why does that happen?", "explain it simply", "explain it like i'm a beginner"]:
            if subject:
                resolved_prompt = f"Explain {subject} simply for a beginner"
                resolved_refs["that"] = subject

        # 5. Handle "This gives IndexError... Fix it."
        elif "fix" in prompt_lower or "indexerror" in prompt_lower or "nullpointerexception" in prompt_lower:
            if last_user_msg and ("code" in last_user_msg.content.lower() or "def " in last_user_msg.content.lower()):
                resolved_prompt = f"Fix the reported code error in: {last_user_msg.content}"
                resolved_refs["error"] = "previous code execution error"

        return resolved_prompt, resolved_refs


global_reference_resolver = ReferenceResolver()
