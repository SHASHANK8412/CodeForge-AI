"""
Per-run LLM usage: real token counts reported by Ollama for every call a generation makes.

GenerationManager sets current_generation_var for the pipeline task; the LLM service calls
record_llm_call after each response. Calls made outside a generation (chat, tools) are not
attributed to any run.
"""

import contextvars
import os
from typing import Any, Optional

current_generation_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "current_generation_var", default=None
)


def _rate(env_name: str) -> float:
    try:
        return float(os.environ.get(env_name, "0") or 0)
    except ValueError:
        return 0.0


def cost_usd(prompt_tokens: int, completion_tokens: int) -> float:
    """
    API cost at the configured per-1K-token rates. Local Ollama models have no API cost, so the
    rates default to 0; set AIFORGE_COST_PER_1K_PROMPT / AIFORGE_COST_PER_1K_COMPLETION to price
    runs as if they used a hosted model.
    """
    return round(prompt_tokens / 1000 * _rate("AIFORGE_COST_PER_1K_PROMPT")
                 + completion_tokens / 1000 * _rate("AIFORGE_COST_PER_1K_COMPLETION"), 6)


def token_counts(response: Any) -> tuple[int, int]:
    """(prompt_tokens, completion_tokens) from an Ollama chat response or final stream chunk."""
    def read(key: str) -> int:
        value = None
        if isinstance(response, dict):
            value = response.get(key)
        else:
            value = getattr(response, key, None)
            if value is None:
                try:
                    value = response[key]
                except Exception:  # noqa: BLE001 - not subscriptable / missing key
                    value = None
        return int(value or 0)

    return read("prompt_eval_count"), read("eval_count")


def record_llm_call(task: str, model: str, prompt_tokens: int, completion_tokens: int,
                    llm_seconds: float, cached: bool = False) -> None:
    gen_id = current_generation_var.get()
    if not gen_id:
        return
    from backend.generation.store import global_generation_store
    global_generation_store.add_usage(gen_id, {
        "agent": task,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "llm_seconds": round(llm_seconds, 3),
        "cached": cached,
    })
