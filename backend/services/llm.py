from __future__ import annotations

import hashlib
import logging
import asyncio
import contextvars
import time
from time import perf_counter
from threading import Lock
from typing import Iterable

from ollama import Client, AsyncClient  # type: ignore[attr-defined]

from backend.config import (
    DEFAULT_NUM_PREDICT,
    DEFAULT_OLLAMA_MODEL,
    MAX_CACHE_ITEMS,
    MAX_PROMPT_CHARS,
    OLLAMA_BASE_OPTIONS,
    OLLAMA_LARGE_MODEL,
    OLLAMA_MEDIUM_MODEL,
    OLLAMA_SMALL_MODEL,
    OLLAMA_CODING_MODEL,
    TASK_NUM_PREDICT,
)
from backend.utils.cache import llm_cache
from backend.utils.retry import async_retry
from backend.utils.prompt_optimizer import optimize_prompt

_ollama_client = Client(timeout=300.0)
_ollama_async_client = AsyncClient(timeout=300.0)

_logger = logging.getLogger("aiforge.performance")

# Context variable to hold an asyncio.Queue for streaming text chunks to SSE
stream_queue_var: contextvars.ContextVar[asyncio.Queue | None] = contextvars.ContextVar("stream_queue_var", default=None)

# Ensure LLM/agent timing logs are actually visible on the console. Without
# a configured handler, Python's logging module silently drops INFO-level
# records (only WARNING+ reach the default "last resort" handler), which is
# why "Agent Start/End", "Execution Time" and "LLM Time" logs previously
# never showed up anywhere.
if not _logger.handlers and not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )
_logger.setLevel(logging.INFO)

_unavailable_models: set[str] = set()


def _normalize_prompt(prompt: str) -> str:
    compact = prompt.strip()
    if len(compact) > MAX_PROMPT_CHARS:
        compact = compact[:MAX_PROMPT_CHARS]
    return compact


def _cache_key(model: str, system_prompt: str, user_prompt: str) -> str:
    raw = f"{model}\n{system_prompt}\n{user_prompt}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _get_cached_response(key: str) -> str | None:
    cached = llm_cache.get(key)
    if cached is not None:
        _logger.info("INFO Cache Hit")
    else:
        _logger.info("INFO Cache Miss")
    return cached


def _set_cached_response(key: str, value: str) -> None:
    llm_cache.set(key, value)


def select_model(task: str, prompt: str = "") -> str:
    task = (task or "").lower()
    prompt = (prompt or "").lower()

    # Medium model: Planner, Architect, Reviewer
    if task in {"planner", "architect", "reviewer"}:
        return OLLAMA_MEDIUM_MODEL

    # Coding model: Frontend, Backend, Database
    if task in {"frontend", "backend", "database"}:
        return OLLAMA_CODING_MODEL

    if task in {"debug", "coding"}:
        if any(keyword in prompt for keyword in ["full stack", "microservice", "architecture", "system", "multi tenant"]):
            return OLLAMA_MEDIUM_MODEL
        return OLLAMA_CODING_MODEL

    # Small model: Explanation, Resume, Documentation, Testing, Github
    if task in {"explanation", "resume", "documentation", "testing", "github"}:
        return OLLAMA_SMALL_MODEL

    if len(prompt) > 2000:
        return OLLAMA_MEDIUM_MODEL

    return DEFAULT_OLLAMA_MODEL


def _generation_options(task: str) -> dict:
    """
    Builds the Ollama `options` payload for a given task: a shared base
    (low temperature/top_p, bounded context window) plus a per-task
    num_predict cap so agents stop generating once their (now much shorter)
    required sections are done instead of producing far more text than
    necessary. Uses lower temperature/top_p values for coding tasks.
    """
    task_lower = (task or "").lower()
    is_coding_task = task_lower in {"frontend", "backend", "database", "coding", "debug"}
    options = {
        "temperature": 0.1 if is_coding_task else 0.2,
        "top_p": 0.9,
        "num_predict": TASK_NUM_PREDICT.get(task_lower, DEFAULT_NUM_PREDICT),
        "num_ctx": 8192
    }
    return options


def _chat_completion(model: str, messages: list[dict[str, str]], stream: bool = False, options: dict | None = None):
    return _ollama_client.chat(
        model=model,
        messages=messages,
        stream=stream,
        options=options or OLLAMA_BASE_OPTIONS,
    )


async def _chat_completion_async(model: str, messages: list[dict[str, str]], stream: bool = False, options: dict | None = None):
    return await _ollama_async_client.chat(
        model=model,
        messages=messages,
        stream=stream,
        options=options or OLLAMA_BASE_OPTIONS,
    )


def _fallback_models(selected_model: str) -> list[str]:
    candidates = [selected_model, DEFAULT_OLLAMA_MODEL, "qwen2.5"]
    ordered_candidates: list[str] = []

    for candidate in candidates:
        if candidate and candidate not in ordered_candidates and candidate not in _unavailable_models:
            ordered_candidates.append(candidate)

    return ordered_candidates


def _chat_completion_with_fallback(
    messages: list[dict[str, str]],
    model: str,
    stream: bool = False,
    options: dict | None = None,
):
    retries = 3
    delay = 0.1
    backoff = 2.0

    for attempt in range(1, retries + 1):
        try:
            last_error: Exception | None = None
            for candidate in _fallback_models(model):
                try:
                    return _chat_completion(candidate, messages, stream=stream, options=options)
                except Exception as exc:  # noqa: BLE001 - Ollama raises ResponseError for missing models.
                    error_text = str(exc).lower()
                    status_code = getattr(exc, "status_code", None)

                    if status_code == 404 or "not found" in error_text or "model" in error_text:
                        _unavailable_models.add(candidate)
                        last_error = exc
                        continue

                    raise

            if last_error is not None:
                raise last_error

            return _chat_completion(model, messages, stream=stream, options=options)
        except Exception as exc:  # noqa: BLE001
            status_code = getattr(exc, "status_code", None)
            error_msg = str(exc).lower()
            is_transient = (
                status_code in {429, 500, 502, 503, 504}
                or "timeout" in error_msg
                or "timed out" in error_msg
                or "connection" in error_msg
                or "rate limit" in error_msg
                or "too many requests" in error_msg
            )
            if not is_transient:
                _logger.error("Permanent LLM failure detected: %s", exc)
                raise exc

            _logger.warning("INFO Retry Attempt %d - Transient error: %s", attempt, exc)
            if attempt < retries:
                import backend.utils.retry as retry_mod
                retry_mod.retries_used_count += 1
                time.sleep(delay)
                delay *= backoff
            else:
                raise exc


@async_retry(retries=3, initial_delay=0.1, backoff_factor=2.0, timeout=300.0)
async def _chat_completion_with_fallback_async(
    messages: list[dict[str, str]],
    model: str,
    stream: bool = False,
    options: dict | None = None,
):
    last_error: Exception | None = None

    for candidate in _fallback_models(model):
        try:
            return await _chat_completion_async(candidate, messages, stream=stream, options=options)
        except Exception as exc:  # noqa: BLE001 - Ollama raises ResponseError for missing models.
            error_text = str(exc).lower()
            status_code = getattr(exc, "status_code", None)

            if status_code == 404 or "not found" in error_text or "model" in error_text:
                _unavailable_models.add(candidate)
                last_error = exc
                continue

            raise

    if last_error is not None:
        raise last_error

    return await _chat_completion_async(model, messages, stream=stream, options=options)


def _generate_message_payload(system_prompt: str, user_prompt: str) -> list[dict[str, str]]:
    messages = []
    if system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt.strip()})
    messages.append({"role": "user", "content": user_prompt})
    return messages


def generate_text(
    system_prompt: str,
    prompt: str,
    model: str | None = None,
    task: str = "general",
) -> str:
    optimized = optimize_prompt(prompt)
    compact_prompt = _normalize_prompt(optimized)
    selected_model = model or select_model(task, compact_prompt)
    key = _cache_key(selected_model, system_prompt, compact_prompt)

    cached = _get_cached_response(key)
    if cached is not None:
        return cached

    _logger.info("Agent Start task=%s model=%s", task, selected_model)
    started_at = perf_counter()
    llm_started_at = perf_counter()
    response = _chat_completion_with_fallback(
        messages=_generate_message_payload(system_prompt, compact_prompt),
        model=selected_model,
        options=_generation_options(task),
    )
    llm_elapsed_ms = (perf_counter() - llm_started_at) * 1000

    content = response["message"]["content"]
    _set_cached_response(key, content)
    elapsed_ms = (perf_counter() - started_at) * 1000
    _logger.info(
        "Agent End task=%s model=%s chars=%d Execution Time=%.1fms LLM Time=%.1fms",
        task,
        selected_model,
        len(compact_prompt),
        elapsed_ms,
        llm_elapsed_ms,
    )
    return content


async def generate_text_async(
    system_prompt: str,
    prompt: str,
    model: str | None = None,
    task: str = "general",
) -> str:
    optimized = optimize_prompt(prompt)
    compact_prompt = _normalize_prompt(optimized)
    selected_model = model or select_model(task, compact_prompt)
    key = _cache_key(selected_model, system_prompt, compact_prompt)

    cached = _get_cached_response(key)
    if cached is not None:
        # If queue is active, we should still push the cached content to SSE stream immediately
        queue = stream_queue_var.get()
        if queue is not None:
            await queue.put(("chunk", task, cached))
        return cached

    started_at = perf_counter()
    llm_started_at = perf_counter()

    queue = stream_queue_var.get()
    if queue is not None:
        _logger.info("Agent Start (stream_async) task=%s model=%s", task, selected_model)
        chunks: list[str] = []
        try:
            stream_response = await _chat_completion_with_fallback_async(
                messages=_generate_message_payload(system_prompt, compact_prompt),
                model=selected_model,
                stream=True,
                options=_generation_options(task),
            )
            async for chunk in stream_response:
                content = chunk.get("message", {}).get("content")
                if content:
                    chunks.append(content)
                    await queue.put(("chunk", task, content))
        except Exception as exc:
            _logger.error("Error in generate_text_async stream: %s", exc)
            raise

        content = "".join(chunks)
    else:
        _logger.info("Agent Start task=%s model=%s", task, selected_model)
        response = await _chat_completion_with_fallback_async(
            messages=_generate_message_payload(system_prompt, compact_prompt),
            model=selected_model,
            stream=False,
            options=_generation_options(task),
        )
        content = response["message"]["content"]

    llm_elapsed_ms = (perf_counter() - llm_started_at) * 1000
    _set_cached_response(key, content)
    elapsed_ms = (perf_counter() - started_at) * 1000
    _logger.info(
        "Agent End task=%s model=%s chars=%d Execution Time=%.1fms LLM Time=%.1fms",
        task,
        selected_model,
        len(compact_prompt),
        elapsed_ms,
        llm_elapsed_ms,
    )
    return content


def generate_response(prompt: str, model: str | None = None, task: str = "general") -> str:
    return generate_text("", prompt, model=model, task=task)


def stream_response(prompt: str, model: str | None = None, task: str = "general") -> Iterable[str]:
    optimized = optimize_prompt(prompt)
    compact_prompt = _normalize_prompt(optimized)
    selected_model = model or select_model(task, compact_prompt)
    cached = _get_cached_response(_cache_key(selected_model, "", compact_prompt))
    if cached is not None:
        yield cached
        return

    started_at = perf_counter()
    chunks: list[str] = []
    for chunk in _chat_completion_with_fallback(
        messages=_generate_message_payload("", compact_prompt),
        model=selected_model,
        stream=True,
        options=_generation_options(task),
    ):
        content = chunk.get("message", {}).get("content")
        if content:
            chunks.append(content)
            yield content

    full_text = "".join(chunks)
    if full_text:
        _set_cached_response(_cache_key(selected_model, "", compact_prompt), full_text)
    _logger.info(
        "Agent End (stream) task=%s model=%s chars=%d LLM Time=%.1fms",
        task,
        selected_model,
        len(compact_prompt),
        (perf_counter() - started_at) * 1000,
    )


def generate_code(
    prompt: str,
    model: str | None = None,
    task: str = "coding",
    system_prompt: str | None = None,
) -> str:
    effective_system_prompt = system_prompt or """
You are an expert software engineer.

Generate clean, production-quality code.

Return only the code unless the user explicitly asks for an explanation.
"""

    optimized = optimize_prompt(prompt)
    compact_prompt = _normalize_prompt(optimized)
    selected_model = model or select_model(task, compact_prompt)
    key = _cache_key(selected_model, effective_system_prompt, compact_prompt)

    cached = _get_cached_response(key)
    if cached is not None:
        return cached

    _logger.info("Agent Start task=%s model=%s", task, selected_model)
    started_at = perf_counter()
    llm_started_at = perf_counter()
    response = _chat_completion_with_fallback(
        messages=_generate_message_payload(effective_system_prompt, compact_prompt),
        model=selected_model,
        options=_generation_options(task),
    )
    llm_elapsed_ms = (perf_counter() - llm_started_at) * 1000

    content = response["message"]["content"]
    _set_cached_response(key, content)
    elapsed_ms = (perf_counter() - started_at) * 1000
    _logger.info(
        "Agent End task=%s model=%s chars=%d Execution Time=%.1fms LLM Time=%.1fms",
        task,
        selected_model,
        len(compact_prompt),
        elapsed_ms,
        llm_elapsed_ms,
    )
    return content


async def generate_code_async(
    prompt: str,
    model: str | None = None,
    task: str = "coding",
    system_prompt: str | None = None,
) -> str:
    effective_system_prompt = system_prompt or """
You are an expert software engineer.

Generate clean, production-quality code.

Return only the code unless the user explicitly asks for an explanation.
"""
    return await generate_text_async(effective_system_prompt, prompt, model=model, task=task)


def stream_code(
    prompt: str,
    model: str | None = None,
    task: str = "coding",
    system_prompt: str | None = None,
):
    effective_system_prompt = system_prompt or """
You are an expert software engineer.

Generate clean, production-quality code.

Return only the code unless the user explicitly asks for an explanation.
"""

    optimized = optimize_prompt(prompt)
    compact_prompt = _normalize_prompt(optimized)
    selected_model = model or select_model(task, compact_prompt)
    cache_key = _cache_key(selected_model, effective_system_prompt, compact_prompt)

    cached = _get_cached_response(cache_key)
    if cached is not None:
        yield cached
        return

    started_at = perf_counter()
    chunks: list[str] = []

    for chunk in _chat_completion_with_fallback(
        messages=_generate_message_payload(effective_system_prompt, compact_prompt),
        model=selected_model,
        stream=True,
        options=_generation_options(task),
    ):
        content = chunk.get("message", {}).get("content")
        if content:
            chunks.append(content)
            yield content

    full_text = "".join(chunks)
    if full_text:
        _set_cached_response(cache_key, full_text)
    _logger.info(
        "Agent End (stream) task=%s model=%s chars=%d LLM Time=%.1fms",
        task,
        selected_model,
        len(compact_prompt),
        (perf_counter() - started_at) * 1000,
    )