from __future__ import annotations

import hashlib
import logging
from collections import OrderedDict
from time import perf_counter
from threading import Lock
from typing import Iterable

from ollama import chat

from backend.config import (
    DEFAULT_OLLAMA_MODEL,
    MAX_CACHE_ITEMS,
    MAX_PROMPT_CHARS,
    OLLAMA_LARGE_MODEL,
    OLLAMA_MEDIUM_MODEL,
    OLLAMA_SMALL_MODEL,
)


_response_cache: OrderedDict[str, str] = OrderedDict()
_cache_lock = Lock()
_logger = logging.getLogger("aiforge.performance")
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
    with _cache_lock:
        cached = _response_cache.get(key)
        if cached is not None:
            _response_cache.move_to_end(key)
        return cached


def _set_cached_response(key: str, value: str) -> None:
    with _cache_lock:
        _response_cache[key] = value
        _response_cache.move_to_end(key)
        while len(_response_cache) > MAX_CACHE_ITEMS:
            _response_cache.popitem(last=False)


def select_model(task: str, prompt: str = "") -> str:
    task = (task or "").lower()
    prompt = (prompt or "").lower()

    if task in {"planner", "architect", "reviewer"}:
        return OLLAMA_MEDIUM_MODEL

    if task in {"debug", "coding"}:
        if any(keyword in prompt for keyword in ["full stack", "microservice", "architecture", "system", "multi tenant"]):
            return OLLAMA_MEDIUM_MODEL
        return OLLAMA_SMALL_MODEL

    if task in {"explanation", "resume"}:
        return OLLAMA_SMALL_MODEL

    if len(prompt) > 2000:
        return OLLAMA_MEDIUM_MODEL

    return DEFAULT_OLLAMA_MODEL


def _chat_completion(model: str, messages: list[dict[str, str]], stream: bool = False):
    return chat(
        model=model,
        messages=messages,
        stream=stream,
    )


def _fallback_models(selected_model: str) -> list[str]:
    candidates = [selected_model, DEFAULT_OLLAMA_MODEL, "qwen2.5"]
    ordered_candidates: list[str] = []

    for candidate in candidates:
        if candidate and candidate not in ordered_candidates and candidate not in _unavailable_models:
            ordered_candidates.append(candidate)

    return ordered_candidates


def _chat_completion_with_fallback(messages: list[dict[str, str]], model: str, stream: bool = False):
    last_error: Exception | None = None

    for candidate in _fallback_models(model):
        try:
            return _chat_completion(candidate, messages, stream=stream)
        except Exception as exc:  # Ollama raises ResponseError for missing models.
            error_text = str(exc).lower()
            status_code = getattr(exc, "status_code", None)

            if status_code == 404 or "not found" in error_text or "model" in error_text:
                _unavailable_models.add(candidate)
                last_error = exc
                continue

            raise

    if last_error is not None:
        raise last_error

    return _chat_completion(model, messages, stream=stream)


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
    compact_prompt = _normalize_prompt(prompt)
    selected_model = model or select_model(task, compact_prompt)
    key = _cache_key(selected_model, system_prompt, compact_prompt)

    cached = _get_cached_response(key)
    if cached is not None:
        _logger.info("LLM cache hit task=%s model=%s chars=%d", task, selected_model, len(compact_prompt))
        return cached

    started_at = perf_counter()
    response = _chat_completion_with_fallback(
        messages=_generate_message_payload(system_prompt, compact_prompt),
        model=selected_model,
    )

    content = response["message"]["content"]
    _set_cached_response(key, content)
    elapsed_ms = (perf_counter() - started_at) * 1000
    _logger.info(
        "LLM generated task=%s model=%s chars=%d ms=%.1f",
        task,
        selected_model,
        len(compact_prompt),
        elapsed_ms,
    )
    return content


def generate_response(prompt: str, model: str | None = None, task: str = "general") -> str:
    return generate_text("", prompt, model=model, task=task)


def stream_response(prompt: str, model: str | None = None, task: str = "general") -> Iterable[str]:
    compact_prompt = _normalize_prompt(prompt)
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
    ):
        content = chunk.get("message", {}).get("content")
        if content:
            chunks.append(content)
            yield content

    full_text = "".join(chunks)
    if full_text:
        _set_cached_response(_cache_key(selected_model, "", compact_prompt), full_text)
    _logger.info(
        "LLM streamed task=%s model=%s chars=%d ms=%.1f",
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

    compact_prompt = _normalize_prompt(prompt)
    selected_model = model or select_model(task, compact_prompt)
    key = _cache_key(selected_model, effective_system_prompt, compact_prompt)

    cached = _get_cached_response(key)
    if cached is not None:
        _logger.info("LLM cache hit task=%s model=%s chars=%d", task, selected_model, len(compact_prompt))
        return cached

    started_at = perf_counter()
    response = _chat_completion_with_fallback(
        messages=_generate_message_payload(effective_system_prompt, compact_prompt),
        model=selected_model,
    )

    content = response["message"]["content"]
    _set_cached_response(key, content)
    elapsed_ms = (perf_counter() - started_at) * 1000
    _logger.info(
        "LLM generated task=%s model=%s chars=%d ms=%.1f",
        task,
        selected_model,
        len(compact_prompt),
        elapsed_ms,
    )
    return content


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

    compact_prompt = _normalize_prompt(prompt)
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
    ):
        content = chunk.get("message", {}).get("content")
        if content:
            chunks.append(content)
            yield content

    full_text = "".join(chunks)
    if full_text:
        _set_cached_response(cache_key, full_text)
    _logger.info(
        "LLM streamed task=%s model=%s chars=%d ms=%.1f",
        task,
        selected_model,
        len(compact_prompt),
        (perf_counter() - started_at) * 1000,
    )