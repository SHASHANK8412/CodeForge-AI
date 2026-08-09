"""
AIForge Context Budget Manager
==============================
Enforces token budgets and priority ordering across generation profiles.
"""

from typing import List, Dict, Any, Tuple
from backend.context.models import ConversationMessage


class ContextBudgetManager:
    """
    Manages context token budget per generation profile.
    """

    PROFILE_BUDGETS = {
        "GENERAL_QA": 1000,
        "EXPLANATION": 1200,
        "CODING": 2500,
        "DEBUGGING": 3000,
        "RAG_QUERY": 2000,
        "PROJECT_GENERATION": 3500,
        "RESUME": 1500,
        "UNKNOWN": 800
    }

    def estimate_tokens(self, text: str) -> int:
        """Lightweight token count estimation (~4 characters per token)."""
        if not text:
            return 0
        return len(text) // 4 + 1

    def format_and_budget_context(
        self,
        user_prompt: str,
        selected_messages: List[ConversationMessage],
        intent: str = "EXPLANATION",
        summary: str = ""
    ) -> Tuple[str, int]:
        max_budget = self.PROFILE_BUDGETS.get(intent, 1500)

        prompt_tokens = self.estimate_tokens(user_prompt)
        remaining_budget = max(200, max_budget - prompt_tokens)

        context_lines = []

        if summary:
            summary_text = f"[Conversation Summary]: {summary}"
            summary_tokens = self.estimate_tokens(summary_text)
            if summary_tokens <= remaining_budget:
                context_lines.append(summary_text)
                remaining_budget -= summary_tokens

        # Format selected messages in chronological order
        msg_lines = []
        for msg in selected_messages:
            role_label = "User" if msg.role == "user" else "Assistant"
            line = f"{role_label}: {msg.content}"
            msg_tokens = self.estimate_tokens(line)

            if msg_tokens <= remaining_budget:
                msg_lines.append(line)
                remaining_budget -= msg_tokens
            else:
                # Truncate older message if necessary
                trunc_chars = remaining_budget * 4
                if trunc_chars > 20:
                    msg_lines.append(f"{role_label}: {msg.content[:trunc_chars]}...")
                break

        if msg_lines:
            context_lines.append("Prior Relevant Conversation Context:")
            context_lines.extend(msg_lines)

        formatted_context = "\n".join(context_lines)
        total_tokens = self.estimate_tokens(user_prompt) + self.estimate_tokens(formatted_context)

        return formatted_context, total_tokens


global_budget_manager = ContextBudgetManager()
