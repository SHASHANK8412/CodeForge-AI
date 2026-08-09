"""
AIForge Topic Tracker & Topic Shift Detector
=============================================
Tracks conversation topic state across turns and detects intentional user topic shifts.
"""

import re
from typing import Dict, Any, List, Tuple
from backend.context.models import ConversationMessage


class TopicTracker:
    """
    Lightweight topic tracker and topic shift detector.
    """

    KNOWN_TOPIC_KEYWORDS = {
        "formula 1": ["formula 1", "f1", "grand prix", "qualifying", "pit stop"],
        "python": ["python"],
        "java": ["java"],
        "c++": ["c++", "cpp"],
        "javascript": ["javascript", "js"],
        "binary search": ["binary search", "bsearch"],
        "merge sort": ["merge sort"],
        "quicksort": ["quicksort"],
        "docker": ["docker", "container", "dockerfile", "image"],
        "kubernetes": ["kubernetes", "k8s", "pod"],
        "fastapi": ["fastapi", "uvicorn"],
        "react": ["react", "jsx", "useState", "useEffect"],
        "photosynthesis": ["photosynthesis", "plant"],
        "sql": ["sql", "join", "postgresql"],
        "resume": ["resume", "cv", "ats"],
        "rag": ["pdf", "uploaded document", "uploaded file"]
    }

    def extract_topic(self, text: str) -> str:
        if not text:
            return ""
        text_lower = text.lower().strip()
        for topic_name, keywords in self.KNOWN_TOPIC_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return topic_name.title()

        # Strip action prefixes
        clean_text = re.sub(r"^(explain|how does|what is|write|implement|build|create|fix|analyze|improve)\s+", "", text_lower).strip()
        clean_text = clean_text.rstrip("?").strip()
        words = clean_text.split()
        if words:
            return " ".join(words).title()
        return text.strip().title()

    def update_topic(
        self,
        current_topic: str,
        user_prompt: str,
        recent_messages: List[ConversationMessage]
    ) -> Tuple[str, bool]:
        """
        Returns (new_topic, topic_shift_detected).
        """
        new_topic_candidate = self.extract_topic(user_prompt)

        # Derive previous topic from recent messages if current_topic not cached
        prev_topic = current_topic
        if not prev_topic and recent_messages:
            last_user_msg = next((m for m in reversed(recent_messages) if m.role == "user"), None)
            if last_user_msg:
                prev_topic = self.extract_topic(last_user_msg.content)

        if not prev_topic:
            return new_topic_candidate, False

        # Check for explicit topic shift
        prompt_lower = user_prompt.lower()
        is_topic_shift = False

        if prev_topic.lower() != new_topic_candidate.lower():
            if any(shift_word in prompt_lower for shift_word in ["explain", "what is", "build", "create", "now let's"]):
                if not any(pron in prompt_lower for pron in ["it", "that", "this", "the code", "the error", "more"]):
                    is_topic_shift = True

        active_topic = new_topic_candidate if is_topic_shift else (prev_topic or new_topic_candidate)
        return active_topic, is_topic_shift


global_topic_tracker = TopicTracker()
