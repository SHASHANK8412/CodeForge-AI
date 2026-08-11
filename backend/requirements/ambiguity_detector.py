"""
AIForge Ambiguity Detector Module
=================================
Identifies ambiguous or unstated requirements in user prompts, ranks them by priority
(CRITICAL, HIGH, MEDIUM, LOW), and surfaces high-value clarifying questions for user review.
"""

import logging
from typing import Dict, Any, List, Optional
from backend.requirements.models import AmbiguityQuestion

_logger = logging.getLogger("aiforge.requirements.ambiguity_detector")


class AmbiguityDetector:
    """
    Detects missing or ambiguous architectural and functional requirements.
    """

    def detect_ambiguities(self, user_prompt: str) -> List[AmbiguityQuestion]:
        prompt_lower = user_prompt.lower()
        questions = []

        if "payment" in prompt_lower or "food" in prompt_lower or "ecommerce" in prompt_lower:
            if not any(k in prompt_lower for k in ["stripe", "razorpay", "paypal"]):
                questions.append(AmbiguityQuestion(
                    id="Q-001",
                    category="PAYMENT_PROVIDER",
                    question="Which payment gateway integration do you prefer?",
                    options=["Stripe", "Razorpay", "Mock Payment Gateway"],
                    importance="CRITICAL",
                    default_choice="Mock Payment Gateway"
                ))

        if "auth" in prompt_lower or "login" in prompt_lower or "user" in prompt_lower:
            if not any(k in prompt_lower for k in ["google", "oauth", "github"]):
                questions.append(AmbiguityQuestion(
                    id="Q-002",
                    category="AUTHENTICATION_TYPE",
                    question="Which authentication methods should be supported?",
                    options=["Email & Password only", "Google OAuth 2.0", "Email/Password + Google OAuth"],
                    importance="HIGH",
                    default_choice="Email & Password only"
                ))

        if not any(k in prompt_lower for k in ["admin", "dashboard", "roles"]):
            questions.append(AmbiguityQuestion(
                id="Q-003",
                category="ADMIN_DASHBOARD",
                question="Do you require an Admin Management Dashboard?",
                options=["No admin dashboard needed", "Yes, include basic admin panel"],
                importance="MEDIUM",
                default_choice="No admin dashboard needed"
            ))

        _logger.info(f"AmbiguityDetector: Found {len(questions)} ambiguity question(s)")
        return questions


global_ambiguity_detector = AmbiguityDetector()
