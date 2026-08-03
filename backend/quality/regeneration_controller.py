"""
AIForge Regeneration Controller Engine
=======================================
Manages controlled, bounded automatic regeneration when LLM outputs fail validation.
Ensures:
1. Max regeneration attempts are bounded (e.g. max 1 attempt by default) to prevent infinite loops.
2. Original user prompt is preserved separately from corrective instructions.
3. Specific, actionable corrective prompts are supplied to the LLM.
4. Appropriate model routing for retries (same model vs fallback model).
"""

import logging
from typing import Dict, Any, Optional, Tuple
from backend.quality.validation_models import ValidationResult, QualityConfig

_logger = logging.getLogger("aiforge.quality.regeneration_controller")


class RegenerationController:
    """
    Regeneration Controller for controlled AI response recovery.
    """

    def __init__(self, config: Optional[QualityConfig] = None):
        self.config = config or QualityConfig()

    def should_regenerate(self, result: ValidationResult, attempt: int) -> bool:
        """
        Determines whether regeneration should proceed based on result status and current attempt count.
        Attempt is 0-indexed (0 = initial generation, 1 = first retry).
        """
        if not result.should_regenerate:
            return False
        if attempt >= self.config.max_regenerations:
            _logger.warning(f"[RegenerationController] Max regeneration limit reached ({attempt}/{self.config.max_regenerations}). Stopping retries.")
            return False
        return True

    def build_corrective_prompt(
        self,
        user_prompt: str,
        failed_response: str,
        result: ValidationResult,
        intent: str,
        agent: str = ""
    ) -> Tuple[str, str]:
        """
        Builds system prompt extension and user prompt wrapper for regeneration.
        Preserves original user prompt separately from corrective instructions.
        Returns: (system_correction, wrapped_user_prompt)
        """
        issues_bullet = "\n".join([f"- {issue}" for issue in result.issues]) if result.issues else "- Response did not meet quality standards."

        intent_upper = (intent or "").upper()
        if intent_upper in ["EXPLANATION", "GENERAL_QA"]:
            correction_rules = (
                "CORRECTIVE INSTRUCTION FOR REGENERATION:\n"
                "Your previous generation failed quality validation due to contract violations:\n"
                f"{issues_bullet}\n\n"
                "REGENERATION MANDATES:\n"
                "1. Answer the original user request directly and naturally.\n"
                "2. Do NOT generate programming source code or function definitions unless explicitly requested.\n"
                "3. Do NOT use competitive programming section headers (e.g., Problem Approach, Algorithmic Approach, Time Complexity).\n"
                "4. Provide a clear, natural explanation matching the user's requested topic."
            )
        elif intent_upper in ["CODING", "DSA_PROBLEM"]:
            correction_rules = (
                "CORRECTIVE INSTRUCTION FOR REGENERATION:\n"
                "Your previous code generation failed validation:\n"
                f"{issues_bullet}\n\n"
                "REGENERATION MANDATES:\n"
                "1. Provide a working, production-ready code implementation answering the original request.\n"
                "2. Ensure the requested programming language and syntax are used correctly.\n"
                "3. Include balanced code fences (```) around code blocks."
            )
        elif intent_upper == "DEBUGGING":
            correction_rules = (
                "CORRECTIVE INSTRUCTION FOR REGENERATION:\n"
                "Your previous debugging response failed validation:\n"
                f"{issues_bullet}\n\n"
                "REGENERATION MANDATES:\n"
                "1. Diagnose the root cause of the reported error clearly.\n"
                "2. Provide actionable fix guidance and corrected code where appropriate.\n"
                "3. Do NOT generate fake algorithm solvers."
            )
        else:
            correction_rules = (
                "CORRECTIVE INSTRUCTION FOR REGENERATION:\n"
                "Your previous response failed quality validation:\n"
                f"{issues_bullet}\n\n"
                "REGENERATION MANDATE:\n"
                "Please regenerate a clean, accurate response directly addressing the original prompt without formatting errors or template leakage."
            )

        wrapped_prompt = (
            f"{user_prompt}\n\n"
            f"[SYSTEM NOTE: {correction_rules}]"
        )

        return correction_rules, wrapped_prompt

    def select_retry_model(self, initial_model: str, attempt: int, intent: str) -> str:
        """
        Selects model for retry attempt.
        First retry (attempt=1) uses the same model with stronger instructions.
        Subsequent retries (if allowed) use Day 3 fallback model if available.
        """
        if attempt <= 1:
            return initial_model

        # Fallback model routing if attempt > 1
        try:
            from backend.models.model_router import global_model_router
            model_sel = global_model_router.select(intent_or_task=intent, agent_name="")
            if model_sel.fallback_models:
                fallback = model_sel.fallback_models[0]
                _logger.info(f"[RegenerationController] Switching to fallback model '{fallback}' for attempt {attempt}")
                return fallback
        except Exception as e:
            _logger.debug(f"[RegenerationController] Model router fallback check skipped: {e}")

        return initial_model


global_regeneration_controller = RegenerationController()
