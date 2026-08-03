"""
AIForge Response Critic Agent
=============================
Evaluates initial candidate responses against original user requests and task plans.
Identifies missing requirements, architectural defects, security gaps, and correctness flaws.
Outputs structured JSON and never exposes private chain-of-thought traces.
"""

import json
import logging
from typing import Dict, Any, List, Optional

from backend.review.models import CritiqueResult, CritiqueIssue
from backend.review.filter import global_critique_filter
from backend.models.model_router import global_model_router
from backend.services.llm import generate_text

_logger = logging.getLogger("aiforge.review.critic_agent")


class ResponseCritic:
    """
    Evaluates candidate responses for completeness, correctness, and architecture quality.
    """

    def critique(
        self,
        user_prompt: str,
        generated_response: str,
        intent: str = "EXPLANATION",
        task_plan: Optional[Any] = None,
        context_result: Optional[Any] = None
    ) -> CritiqueResult:
        if not user_prompt or not generated_response:
            return CritiqueResult(needs_revision=False, score=1.0, is_valid=True)

        try:
            # Deterministic requirement audit first (fast & reliable)
            missing_reqs = self._audit_explicit_requirements(user_prompt, generated_response)

            if missing_reqs:
                _logger.info(f"[ResponseCritic] Deterministic audit found missing requirements: {missing_reqs}")
                issues = [
                    CritiqueIssue(
                        category="REQUIREMENT_MISSING",
                        severity="high",
                        description=f"Explicit requirement '{req}' is missing from response.",
                        suggested_action=f"Add complete implementation and explanation for '{req}'."
                    )
                    for req in missing_reqs
                ]
                raw_critique = CritiqueResult(
                    needs_revision=True,
                    score=0.70,
                    issues=issues,
                    strengths=["Response is partially complete."],
                    missing_requirements=missing_reqs,
                    priority="high",
                    is_valid=True
                )
                return global_critique_filter.filter_critique(user_prompt, raw_critique)

            # If response passed deterministic audit, evaluate using model router if complex
            model_selection = global_model_router.select(intent_or_task=intent, agent_name="ReviewerAgent")
            model_name = model_selection.selected_model

            # Construct structured critic prompt
            system_prompt = (
                "You are AIForge's Senior Code & Architecture Critic Agent.\n"
                "Evaluate the provided candidate response against the original user request.\n"
                "Focus ONLY on:\n"
                "1. Missing explicit requirements\n"
                "2. Incorrect code or architecture flaws\n"
                "3. Obvious security gaps (e.g. missing token revocation, plaintext passwords)\n\n"
                "DO NOT complain about style, formatting, or unrequested features.\n"
                "Respond ONLY with valid JSON in this format:\n"
                "{\n"
                '  "needs_revision": false,\n'
                '  "score": 0.95,\n'
                '  "issues": [],\n'
                '  "strengths": ["Clear explanation"],\n'
                '  "missing_requirements": []\n'
                "}"
            )

            prompt_content = f"ORIGINAL USER REQUEST:\n{user_prompt}\n\nCANDIDATE RESPONSE:\n{generated_response[:2000]}"

            raw_response = generate_text(
                system_prompt=system_prompt,
                prompt=prompt_content,
                model=model_name,
                task="review"
            )

            # Parse structured JSON output
            json_str = raw_response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()

            parsed = json.loads(json_str)
            if not isinstance(parsed, dict):
                parsed = {}

            parsed_issues = [
                CritiqueIssue(
                    category=iss.get("category", "CORRECTNESS"),
                    severity=iss.get("severity", "medium"),
                    description=iss.get("description", ""),
                    suggested_action=iss.get("suggested_action", "")
                )
                for iss in parsed.get("issues", [])
            ]

            critique = CritiqueResult(
                needs_revision=parsed.get("needs_revision", False),
                score=float(parsed.get("score", 0.90)),
                issues=parsed_issues,
                strengths=parsed.get("strengths", []),
                missing_requirements=parsed.get("missing_requirements", []),
                priority="high" if parsed.get("needs_revision", False) else "low",
                is_valid=True
            )

            return global_critique_filter.filter_critique(user_prompt, critique)

        except Exception as e:
            _logger.warning(f"[ResponseCritic] Critic execution encountered error/fallback: {e}; preserving original response")
            return CritiqueResult(needs_revision=False, score=1.0, is_valid=False)

    def _audit_explicit_requirements(self, prompt: str, response: str) -> List[str]:
        """Performs fast deterministic requirement audit against response."""
        prompt_lower = prompt.lower()
        response_lower = response.lower()
        missing = []

        keywords_to_check = [
            ("revocation", ["revocation", "revoke"]),
            ("logout", ["logout", "blacklisted"]),
            ("refresh token", ["refresh token", "refresh_token"]),
            ("access token", ["access token", "access_token"]),
            ("role-based", ["role", "rbac", "permission"]),
            ("postgres", ["postgres", "postgresql", "sqlalchemy"]),
            ("redis", ["redis"]),
            ("jwt", ["jwt", "bearer", "payload"])
        ]

        for req_label, search_terms in keywords_to_check:
            if any(term in prompt_lower for term in search_terms):
                if not any(term in response_lower for term in search_terms):
                    missing.append(req_label)

        return missing


global_response_critic = ResponseCritic()
