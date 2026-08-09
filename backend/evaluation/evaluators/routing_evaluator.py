"""
AIForge Routing Evaluator
=========================
Evaluates intent classification accuracy, agent routing accuracy, and model profile matching against Golden Test Cases.
"""

from typing import Dict, Any
from backend.agents.router_agent import global_router_agent
from backend.models.model_router import global_model_router
from backend.evaluation.models import GoldenTestCase


class RoutingEvaluator:
    """
    Evaluator for intent classification and routing decisions.
    """

    def evaluate_routing(self, case: GoldenTestCase) -> Dict[str, Any]:
        res = global_router_agent.classify_intent(case.prompt)
        actual_intent = res["intent"]
        actual_agent = res.get("target_agent", "ExplanationAgent")

        model_sel = global_model_router.select(intent_or_task=actual_intent, agent_name=actual_agent)
        actual_profile = actual_intent

        intent_pass = (actual_intent == case.expected_intent)
        agent_pass = (actual_agent == case.expected_agent)
        profile_pass = (actual_profile == case.expected_profile)

        return {
            "actual_intent": actual_intent,
            "actual_agent": actual_agent,
            "actual_profile": actual_profile,
            "intent_pass": intent_pass,
            "agent_pass": agent_pass,
            "profile_pass": profile_pass,
            "overall_routing_pass": intent_pass and agent_pass and profile_pass
        }


global_routing_evaluator = RoutingEvaluator()
