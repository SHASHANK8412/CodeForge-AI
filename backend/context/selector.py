"""
AIForge Context Selector
========================
Selects relevant conversation turns and filters irrelevant history based on recency,
semantic topic matching, follow-up status, and topic shifts.
"""

from typing import List, Dict, Any
from backend.context.models import ConversationMessage


class ContextSelector:
    """
    Selects relevant messages from conversation history while excluding topic-shifted history.
    """

    def select_messages(
        self,
        messages: List[ConversationMessage],
        is_follow_up: bool,
        topic_shift: bool,
        current_topic: str = "",
        max_messages: int = 6
    ) -> List[ConversationMessage]:
        if not messages:
            return []

        # If a topic shift occurred, drop irrelevant past history from active generation context
        if topic_shift:
            return []

        if not is_follow_up:
            # For independent requests within an ongoing chat, include at most the last 2 turns if topic matches
            filtered = []
            for msg in reversed(messages[-4:]):
                if current_topic and current_topic.lower() in msg.content.lower():
                    filtered.insert(0, msg)
            return filtered[-2:]

        # For follow-ups, select recent turns up to max_messages
        selected = messages[-max_messages:]
        return selected


global_context_selector = ContextSelector()
