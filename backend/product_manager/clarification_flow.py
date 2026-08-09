"""
AIForge Requirement Clarification Flow (Day 50)
==============================================
Generates targeted clarifying questions to refine underspecified user ideas before SRS generation.
"""

import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.product_manager.clarification_flow")


class ClarificationFlowGenerator:
    """
    Generates targeted clarification questions for ambiguous user prompts.
    """

    def generate_clarifying_questions(self, raw_prompt: str) -> List[Dict[str, Any]]:
        """
        Returns structured clarification questions based on key project categories.
        """
        questions = [
            {
                "id": "q1",
                "category": "Target Audience & Scale",
                "question": "What is the expected initial user base and growth target (e.g. 10K vs 10M users)?",
                "default_option": "100K active users"
            },
            {
                "id": "q2",
                "category": "Authentication",
                "question": "Which authentication mechanisms are required (OAuth2, Social Login, Multi-Factor Auth)?",
                "default_option": "Stateless OAuth2 + JWT"
            },
            {
                "id": "q3",
                "category": "Monetization / Payment",
                "question": "Will the app integrate payment gateways (Stripe, PayPal, Subscription tiers)?",
                "default_option": "Stripe Subscriptions & One-time checkout"
            }
        ]

        _logger.info(f"ClarificationFlowGenerator: Generated {len(questions)} clarifying questions for '{raw_prompt}'")
        return questions


global_clarification_flow = ClarificationFlowGenerator()
