"""
AIForge Quality Recovery Day 14 — Centralized LLM Client & Service Layer
========================================================================
Centralized client managing LLM invocations with bounded timeouts, retries,
circuit breaking, connection reuse, fallback models, and telemetry.
"""

import time
import logging
from typing import Dict, Any, Optional

from backend.services.llm import global_llm_service
from backend.performance.config import global_performance_config
from backend.performance.resilience import global_retry_policy, global_circuit_breaker_registry, global_fallback_policy
from backend.performance.tracer import global_request_tracer
from backend.performance.cache_manager import global_cache_manager

logger = logging.getLogger("aiforge.performance.llm_client")


class CentralizedLLMClient:
    """
    Centralized LLM invocation gateway.
    Handles timeouts, retries, circuit breaking, caching, model tier routing,
    and metrics across all AIForge agents.
    """

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model_name: Optional[str] = None,
        model_tier: str = "standard",
        request_id: Optional[str] = None,
        use_cache: bool = True,
        timeout: Optional[float] = None
    ) -> str:
        """
        Main entry point for generating completions with resiliency and performance controls.
        """
        # 1. Determine model target
        target_model = model_name or ("qwen2.5-coder:7b" if model_tier == "strong" else "qwen2.5-coder:1.5b")
        t_out = timeout or global_performance_config.LLM_READ_TIMEOUT_SECONDS

        # 2. Check cache if enabled
        cache_key = None
        if use_cache and global_performance_config.AIFORGE_CACHE_ENABLED:
            cache_key = global_cache_manager.build_key(
                prompt_or_text=f"{system_prompt or ''}:{prompt}",
                namespace="llm",
                model=target_model
            )
            cached_resp = global_cache_manager.get("llm", cache_key)
            if cached_resp:
                if request_id:
                    global_request_tracer.record_cache_hit(request_id)
                logger.info(f"[{request_id or 'NO_REQ'}] LLM cache hit for model '{target_model}'")
                return cached_resp

        # 3. Check Circuit Breaker
        cb = global_circuit_breaker_registry.get("ollama")
        if global_performance_config.AIFORGE_CIRCUIT_BREAKER_ENABLED and not cb.allow_request():
            logger.warning(f"[{request_id or 'NO_REQ'}] Circuit 'ollama' is OPEN. Falling back to local synthesis.")
            return f"AIForge (Degraded Mode): Local LLM service is temporarily unavailable. Primary prompt processed: {prompt[:100]}..."

        # 4. Invocations with Retries and Telemetry
        def _invoke_primary() -> str:
            if request_id:
                global_request_tracer.record_model_call(request_id)
            return global_llm_service.generate_completion(
                prompt=prompt,
                system_prompt=system_prompt,
                model_name=target_model,
                timeout=t_out
            )

        def _invoke_fallback() -> str:
            # Fallback model or synthesis if primary model fails
            logger.warning(f"[{request_id or 'NO_REQ'}] Primary LLM failed or timed out. Executing fallback completion.")
            return global_llm_service.generate_completion(
                prompt=prompt,
                system_prompt=system_prompt,
                model_name="qwen2.5-coder:1.5b",
                timeout=15.0
            )

        try:
            resp = global_retry_policy.execute_with_retry(
                func=_invoke_primary,
                max_retries=global_performance_config.MAX_RETRIES,
                stage_name="LLM_GENERATE"
            )
            cb.record_success()

            # Cache successful response if deterministic
            if cache_key and resp:
                global_cache_manager.put("llm", cache_key, resp)

            return resp
        except Exception as ex:
            cb.record_failure()
            logger.warning(f"[{request_id or 'NO_REQ'}] LLM invocation failed after retries: {ex}")

            # Attempt fallback model
            try:
                fb_resp, _ = global_fallback_policy.execute_with_fallback(
                    primary_func=_invoke_fallback,
                    fallback_func=lambda: f"AIForge Fallback: Unable to complete request due to model service error: {ex}",
                    circuit_name="ollama"
                )
                return fb_resp
            except Exception as fb_ex:
                return f"AIForge Error: LLM completion service unavailable ({fb_ex})."


global_llm_client = CentralizedLLMClient()
