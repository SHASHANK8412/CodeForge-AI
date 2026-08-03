"""
AIForge Follow-Up Detector
==========================
Detects whether a user request is a follow-up depending on prior conversation context.
Deterministic & pattern-based detection prevents unnecessary LLM overhead.
"""

import re
from typing import Dict, Any, List, Optional
from backend.context.models import ConversationMessage


class FollowUpDetector:
    """
    Detects follow-up intent and contextual dependency.
    """

    FOLLOW_UP_PATTERNS = [
        r"\bmake it\b",
        r"\bchange it\b",
        r"\bconvert it\b",
        r"\brewrite it\b",
        r"\bshow me the\b",
        r"\bexplain (that|it|this|the code|the error)\b",
        r"\bexplain it like\b",
        r"\bexplain .* in more detail\b",
        r"\bwhy(\?|\s|$)",
        r"\bhow does .* work(\?|\s|$)",
        r"\bwhat about\b",
        r"\bgive another\b",
        r"\bfix (the|this|that|it)\b",
        r"\boptimize (it|that|the code|the function)\b",
        r"\badd (a|an|jwt|auth|endpoint|test|feature|refresh|rotation|revocation|role)\b",
        r"\bnow add\b",
        r"\balso add\b",
        r"\bnow update\b",
        r"\bthis (gives|throws|fails|crashes|returns)\b",
        r"\bwhy does (this|that|it) (fail|crash|happen|occur)\b",
        r"\bwhat does it say\b",
        r"\bis that correct\b",
        r"\bmore simply\b",
        r"\bcan you clarify\b",
    ]

    TOPIC_SHIFT_PATTERNS = [
        r"\banyway\b",
        r"\bdifferent question\b",
        r"\bmoving on\b",
        r"\bnew topic\b",
        r"\bnow let's talk about\b",
        r"\bnow explain\b",
        r"\bexplain formula 1\b",
        r"\bexplain photosynthesis\b",
        r"\bexplain docker\b",
        r"\bexplain kubernetes\b",
        r"\bexplain rest apis\b",
        r"\bbuild a\b",
        r"\bgenerate a\b",
    ]

    def detect(
        self,
        user_prompt: str,
        recent_messages: List[ConversationMessage],
        current_topic: str = ""
    ) -> Dict[str, Any]:
        if not recent_messages:
            return {"is_follow_up": False, "confidence": 0.0, "reason": "No conversation history"}

        prompt_lower = user_prompt.strip().lower()

        # 1. Check Explicit Topic Shift Patterns
        for shift_pat in self.TOPIC_SHIFT_PATTERNS:
            if re.search(shift_pat, prompt_lower):
                # If it's "now explain X" where X is a major topic, treat as topic shift
                if not any(pron in prompt_lower for pron in ["it", "that", "this", "the previous"]):
                    return {
                        "is_follow_up": False,
                        "confidence": 0.95,
                        "reason": f"Matched explicit topic shift pattern: '{shift_pat}'"
                    }

        # 2. Check Very Short Ambiguous Inputs ("Why?", "How?", "More details", "Make it Java")
        if len(prompt_lower.split()) <= 4:
            if any(w in prompt_lower for w in ["why", "how", "what", "more", "java", "python", "fix"]):
                return {
                    "is_follow_up": True,
                    "confidence": 0.95,
                    "reason": "Short contextual prompt requiring previous turn history"
                }

        # 3. Check Follow-up Patterns
        for pat in self.FOLLOW_UP_PATTERNS:
            if re.search(pat, prompt_lower):
                return {
                    "is_follow_up": True,
                    "confidence": 0.90,
                    "reason": f"Matched follow-up pattern: '{pat}'"
                }

        # 4. Check Pronoun and Demonstrative References
        if any(ref in prompt_lower for ref in [" it ", " that ", " this ", " the code ", " the function ", " the error ", " the file "]):
            return {
                "is_follow_up": True,
                "confidence": 0.85,
                "reason": "Contains pronoun or demonstrative reference"
            }

        # 5. Check Subject Continuity with Current Topic
        if current_topic and current_topic.lower() in prompt_lower:
            return {
                "is_follow_up": True,
                "confidence": 0.80,
                "reason": f"References active conversation topic: '{current_topic}'"
            }

        return {"is_follow_up": False, "confidence": 0.20, "reason": "Independent query"}


global_followup_detector = FollowUpDetector()
