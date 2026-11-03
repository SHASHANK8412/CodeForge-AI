"""
Groq as the model provider for AIForge's coding agents.

When GROQ_API_KEY is set, the tasks in AIFORGE_GROQ_TASKS (by default the code-writing agents: architect,
frontend, backend, database and the debug/patch steps) are answered by a model hosted on Groq
(AIFORGE_GROQ_MODEL, default openai/gpt-oss-120b) through Groq's OpenAI-compatible chat API. Every other task
stays on the local Ollama models. Without a key nothing changes and no prompt leaves the machine.

If a Groq call fails (network, rate limit, bad key), the caller falls back to the local model, so a run still
gets a real answer; the failure is logged. The key is read from the environment, or from GROQ_API_KEY in the
repository's .env file, and is never logged.

Settings (environment variables):
  GROQ_API_KEY                  required to enable Groq
  AIFORGE_GROQ_MODEL            Groq model id (default openai/gpt-oss-120b)
  AIFORGE_GROQ_TASKS            comma-separated tasks to send to Groq (default: the coding agents)
  AIFORGE_GROQ_TIMEOUT_SECONDS  per-call timeout (default 120)
  AIFORGE_GROQ_REASONING_EFFORT low | medium | high, for reasoning models such as gpt-oss (default medium)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

_logger = logging.getLogger("aiforge.performance")

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-120b"
DEFAULT_TASKS = ("architect", "frontend", "backend", "database", "coding", "debug", "debugging", "testing")
# Reasoning models spend part of the completion budget thinking; this keeps room for the actual answer.
MIN_COMPLETION_TOKENS = 8192
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class GroqError(RuntimeError):
    """A Groq call that did not produce an answer (the caller falls back to the local model)."""


@dataclass
class GroqResult:
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int


def _api_key() -> str:
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if key or not _ENV_FILE.is_file():
        return key
    try:  # only this one value is read from .env; nothing else is loaded into the environment
        from dotenv import dotenv_values
        return (dotenv_values(_ENV_FILE).get("GROQ_API_KEY") or "").strip()
    except Exception:  # noqa: BLE001 - an unreadable .env just means Groq stays off
        return ""


def model() -> str:
    return os.environ.get("AIFORGE_GROQ_MODEL", "").strip() or DEFAULT_MODEL


def groq_tasks() -> tuple[str, ...]:
    raw = os.environ.get("AIFORGE_GROQ_TASKS")
    if raw is None:
        return DEFAULT_TASKS
    return tuple(t.strip().lower() for t in raw.split(",") if t.strip())


def handles(task: str) -> bool:
    """True when this task should be answered by Groq: a key is configured and the task is a Groq task."""
    return bool(_api_key()) and (task or "").lower() in groq_tasks()


def _payload(messages: list[dict[str, str]], options: Optional[dict]) -> dict:
    options = options or {}
    body = {
        "model": model(),
        "messages": messages,
        "temperature": options.get("temperature", 0.2),
        "top_p": options.get("top_p", 0.9),
        "max_completion_tokens": max(int(options.get("num_predict") or 0), MIN_COMPLETION_TOKENS),
    }
    if "gpt-oss" in body["model"]:
        body["reasoning_effort"] = os.environ.get("AIFORGE_GROQ_REASONING_EFFORT", "medium")
    return body


def _parse(response: httpx.Response) -> GroqResult:
    if response.status_code != 200:
        detail = ""
        try:
            detail = (response.json().get("error") or {}).get("message", "")
        except ValueError:
            detail = response.text[:200]
        raise GroqError(f"Groq answered HTTP {response.status_code}: {detail}".strip())
    data = response.json()
    choice = (data.get("choices") or [{}])[0]
    content = ((choice.get("message") or {}).get("content") or "").strip()
    if not content:
        raise GroqError(f"Groq returned an empty answer (finish_reason={choice.get('finish_reason')})")
    usage = data.get("usage") or {}
    return GroqResult(content=content, model=data.get("model") or model(),
                      prompt_tokens=int(usage.get("prompt_tokens") or 0),
                      completion_tokens=int(usage.get("completion_tokens") or 0))


def _timeout() -> float:
    try:
        return float(os.environ.get("AIFORGE_GROQ_TIMEOUT_SECONDS", "120"))
    except ValueError:
        return 120.0


def chat(messages: list[dict[str, str]], options: Optional[dict] = None,
         transport: Optional[httpx.BaseTransport] = None) -> GroqResult:
    headers = {"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"}
    try:
        with httpx.Client(timeout=_timeout(), transport=transport) as client:
            return _parse(client.post(GROQ_CHAT_URL, json=_payload(messages, options), headers=headers))
    except httpx.HTTPError as exc:
        raise GroqError(f"Groq request failed: {type(exc).__name__}") from exc


async def chat_async(messages: list[dict[str, str]], options: Optional[dict] = None,
                     transport: Optional[httpx.AsyncBaseTransport] = None) -> GroqResult:
    headers = {"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=_timeout(), transport=transport) as client:
            return _parse(await client.post(GROQ_CHAT_URL, json=_payload(messages, options), headers=headers))
    except httpx.HTTPError as exc:
        raise GroqError(f"Groq request failed: {type(exc).__name__}") from exc


def status() -> dict:
    """What the app reports about Groq (never the key itself)."""
    enabled = bool(_api_key())
    return {"enabled": enabled, "model": model() if enabled else None, "tasks": list(groq_tasks()) if enabled else []}
