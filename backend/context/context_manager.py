"""
AIForge Conversation Context Manager
====================================
Centralized orchestrator for multi-turn conversation intelligence:
1. Loads conversation history isolated strictly by conversation_id.
2. Detects follow-ups vs independent topics vs topic shifts.
3. Resolves ambiguous references ("it", "that", "the code", "the error").
4. Tracks active topic across turns.
5. Selects relevant history and excludes topic-shifted context.
6. Enforces context token budgets.
7. Produces a typed ContextResult for IntentClassifier and Specialized Agents.
"""

import logging
from typing import Dict, Any, List, Optional
from backend.memory.conversation_manager import ConversationManager
from backend.context.models import ConversationMessage, ContextResult
from backend.context.followup_detector import global_followup_detector
from backend.context.reference_resolver import global_reference_resolver
from backend.context.topic_tracker import global_topic_tracker
from backend.context.selector import global_context_selector
from backend.context.budget_manager import global_budget_manager

_logger = logging.getLogger("aiforge.context.context_manager")


class ConversationContextManager:
    """
    Centralized Conversation Context Manager for AIForge V2.
    """

    def __init__(self, conversation_manager: Optional[ConversationManager] = None):
        self.conv_mgr = conversation_manager or ConversationManager()
        self._topic_cache: Dict[str, str] = {}

    def get_context(
        self,
        conversation_id: Optional[str],
        user_prompt: str
    ) -> ContextResult:
        if not conversation_id:
            return ContextResult(
                conversation_id="",
                is_follow_up=False,
                topic=global_topic_tracker.extract_topic(user_prompt),
                topic_shift=False,
                resolved_references={},
                resolved_prompt=user_prompt,
                formatted_context="",
                selected_messages=[],
                summary="",
                estimated_tokens=global_budget_manager.estimate_tokens(user_prompt)
            )

        # 1. Load Conversation Messages from Repository (Strictly Isolated by conversation_id)
        msg_records = self.conv_mgr.get_messages(conversation_id, limit=20)
        messages = [
            ConversationMessage(
                id=m.message_id,
                role=m.role,
                content=m.content,
                timestamp=m.timestamp,
                metadata=m.metadata or {}
            )
            for m in msg_records
        ]

        current_topic = self._topic_cache.get(conversation_id, "")

        # 2. Topic Tracking & Shift Detection
        new_topic, topic_shift = global_topic_tracker.update_topic(
            current_topic=current_topic,
            user_prompt=user_prompt,
            recent_messages=messages
        )
        self._topic_cache[conversation_id] = new_topic

        # 3. Follow-Up Detection
        followup_info = global_followup_detector.detect(
            user_prompt=user_prompt,
            recent_messages=messages,
            current_topic=new_topic
        )
        is_follow_up = followup_info["is_follow_up"] and not topic_shift

        # 4. Reference Resolution
        resolved_prompt, resolved_refs = global_reference_resolver.resolve(
            user_prompt=user_prompt,
            recent_messages=messages,
            current_topic=new_topic
        )

        # 5. Context Selection (Excludes history if topic_shift is True)
        selected_msgs = global_context_selector.select_messages(
            messages=messages,
            is_follow_up=is_follow_up,
            topic_shift=topic_shift,
            current_topic=new_topic
        )

        # 6. Context Budgeting & Formatting
        formatted_ctx, est_tokens = global_budget_manager.format_and_budget_context(
            user_prompt=user_prompt,
            selected_messages=selected_msgs
        )

        _logger.info(
            f"[AIForge Context] ConvID: {conversation_id[:8]} | FollowUp: {is_follow_up} | "
            f"Topic: '{new_topic}' | TopicShift: {topic_shift} | SelectedMsgs: {len(selected_msgs)} | Tokens: {est_tokens}"
        )

        return ContextResult(
            conversation_id=conversation_id,
            is_follow_up=is_follow_up,
            follow_up_confidence=followup_info["confidence"],
            topic=new_topic,
            topic_shift=topic_shift,
            resolved_references=resolved_refs,
            resolved_prompt=resolved_prompt,
            formatted_context=formatted_ctx,
            selected_messages=selected_msgs,
            summary="",
            estimated_tokens=est_tokens
        )


global_context_manager = ConversationContextManager()
