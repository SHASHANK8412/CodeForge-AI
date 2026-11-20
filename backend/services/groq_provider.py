"""
Groq as the model provider for AIForge's agents.

When GROQ_API_KEY is set, the tasks in AIFORGE_GROQ_TASKS (by default all of them: code generation, planning, review,
testing, debugging, documentation and chat) are answered by a model hosted on Groq (AIFORGE_GROQ_MODEL, default
qwen/qwen3.8-27b, Qwen 3.8 27B) through Groq's OpenAI-compatible chat API. Tasks not listed stay on the local Ollama
models, and embeddings are always local. Without a key nothing changes and no prompt leaves the machine.

Qwen 3.8 is a reasoning model: its thinking is requested hidden (reasoning_format=hidden), so only the final answer -
the code - reaches the agents; any <think> block that still arrives is removed.

If a Groq call fails (network, rate limit, bad key), the caller falls back to the local model, so a run still
gets a real answer; the failure is logged. The key is read from the environment, or from GROQ_API_KEY in the
repository's .env file, and is never logged.

Settings (environment variables):
  GROQ_API_KEY                  required to enable Groq
  AIFORGE_GROQ_MODEL            Groq model id (default qwen/qwen3.8-27b; e.g. openai/gpt-oss-120b)
  AIFORGE_GROQ_TASKS            comma-separated tasks to send to Groq, or "all" (default all)
  AIFORGE_GROQ_TIMEOUT_SECONDS  per-call timeout (default 120)
  AIFORGE_GROQ_REASONING_EFFORT reasoning depth: for gpt-oss low | medium | high (default medium); for Qwen
                                none | default | low | medium | high (default "default": thinking on)
  AIFORGE_GROQ_RATE_LIMIT_WAIT  seconds a call may wait in total when Groq says "rate limited, try again in N s"
                                (default 60); after that the caller falls back to the local model

Rate limits: Groq accounts have a tokens-per-minute limit (8,000 on some on-demand tiers, about four agent calls).
A rate-limited call waits the time Groq asks for and retries, instead of falling back to the local model at once.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

_logger = logging.getLogger("aiforge.performance")

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "qwen/qwen3.8-27b"
DEFAULT_TASKS = ("all",)
_THINK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL | re.IGNORECASE)
# Reasoning models spend part of the completion budget thinking; this keeps room for the actual answer.
MIN_COMPLETION_TOKENS = 8192
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class GroqError(RuntimeError):
    """A Groq call that did not produce an answer (the caller falls back to the local model)."""


class GroqRateLimited(GroqError):
    def __init__(self, message: str, retry_after: Optional[float]):
        super().__init__(message)
        self.retry_after = retry_after


def _retry_after(response: httpx.Response, detail: str) -> Optional[float]:
    """Seconds Groq asks us to wait: the Retry-After header, or "try again in 1.5s" / "in 2m3.5s" in the message."""
    header = response.headers.get("retry-after")
    if header:
        try:
            return float(header)
        except ValueError:
            pass
    m = re.search(r"try again in (?:(\d+)m)?(\d+(?:\.\d+)?)s", detail or "")
    if m:
        return float(m.group(1) or 0) * 60 + float(m.group(2))
    return None


def _rate_limit_budget() -> float:
    try:
        return float(os.environ.get("AIFORGE_GROQ_RATE_LIMIT_WAIT", "60"))
    except ValueError:
        return 60.0


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
    tasks = groq_tasks()
    return bool(_api_key()) and ("all" in tasks or "*" in tasks or (task or "").lower() in tasks)


def _payload(messages: list[dict[str, str]], options: Optional[dict]) -> dict:
    options = options or {}
    body = {
        "model": model(),
        "messages": messages,
        "temperature": options.get("temperature", 0.2),
        "top_p": options.get("top_p", 0.9),
        "max_completion_tokens": max(int(options.get("num_predict") or 0), MIN_COMPLETION_TOKENS),
    }
    effort = os.environ.get("AIFORGE_GROQ_REASONING_EFFORT", "").strip().lower()
    if "gpt-oss" in body["model"]:
        body["reasoning_effort"] = effort or "medium"
    elif "qwen" in body["model"].lower():
        body["reasoning_effort"] = effort or "default"
        body["reasoning_format"] = "hidden"             # only the answer comes back, not the thinking
    return body


def _parse(response: httpx.Response) -> GroqResult:
    if response.status_code != 200:
        detail = ""
        try:
            detail = (response.json().get("error") or {}).get("message", "")
        except ValueError:
            detail = response.text[:200]
        message = f"Groq answered HTTP {response.status_code}: {detail}".strip()
        if response.status_code == 429:
            raise GroqRateLimited(message, _retry_after(response, detail))
        raise GroqError(message)
    data = response.json()
    choice = (data.get("choices") or [{}])[0]
    content = _THINK_RE.sub("", (choice.get("message") or {}).get("content") or "").strip()
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


def _wait_for(exc: GroqRateLimited, waited: float) -> Optional[float]:
    """How long to wait before retrying a rate-limited call, or None when the wait budget is used up."""
    wait = (exc.retry_after if exc.retry_after is not None else 5.0) + 0.25
    return wait if waited + wait <= _rate_limit_budget() else None


def chat(messages: list[dict[str, str]], options: Optional[dict] = None,
         transport: Optional[httpx.BaseTransport] = None, sleep=None) -> GroqResult:
    import time
    sleep = sleep or time.sleep
    headers = {"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"}
    waited = 0.0
    while True:
        try:
            with httpx.Client(timeout=_timeout(), transport=transport) as client:
                return _parse(client.post(GROQ_CHAT_URL, json=_payload(messages, options), headers=headers))
        except GroqRateLimited as exc:
            wait = _wait_for(exc, waited)
            if wait is None:
                raise
            _logger.info("Groq rate limit: waiting %.1fs before retrying", wait)
            sleep(wait)
            waited += wait
        except httpx.HTTPError as exc:
            raise GroqError(f"Groq request failed: {type(exc).__name__}") from exc


async def chat_async(messages: list[dict[str, str]], options: Optional[dict] = None,
                     transport: Optional[httpx.AsyncBaseTransport] = None, sleep=None) -> GroqResult:
    import asyncio
    sleep = sleep or asyncio.sleep
    headers = {"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"}
    waited = 0.0
    while True:
        try:
            async with httpx.AsyncClient(timeout=_timeout(), transport=transport) as client:
                return _parse(await client.post(GROQ_CHAT_URL, json=_payload(messages, options), headers=headers))
        except GroqRateLimited as exc:
            wait = _wait_for(exc, waited)
            if wait is None:
                raise
            _logger.info("Groq rate limit: waiting %.1fs before retrying", wait)
            await sleep(wait)
            waited += wait
        except httpx.HTTPError as exc:
            raise GroqError(f"Groq request failed: {type(exc).__name__}") from exc


def status() -> dict:
    """What the app reports about Groq (never the key itself)."""
    enabled = bool(_api_key())
    return {"enabled": enabled, "model": model() if enabled else None, "tasks": list(groq_tasks()) if enabled else []}
