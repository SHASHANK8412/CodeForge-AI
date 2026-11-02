"""
Structured tracing for AIForge agents and LLM calls.

Every LLM call and every LangGraph node emits one JSON event. Events go to:

* an in-process collector (``TraceCollector``) that the benchmark harness reads
  to compute per-task latency, token usage, cache hits and fallback usage;
* optionally a JSONL file, enabled with ``AIFORGE_TRACE_FILE=/path/trace.jsonl``.

Design notes
------------
* Token counts come from the provider when it reports them (Ollama returns
  ``prompt_eval_count`` / ``eval_count``). When it does not, we fall back to a
  chars/4 estimate and mark the event ``tokens_estimated=True`` so reports never
  present an estimate as a measurement.
* A "fallback" is when the LLM call failed and ``backend.services.llm`` returned
  canned placeholder output. Benchmarks treat any fallback as an invalid run,
  because canned output can look like a successful generation.
* Prompts/outputs are truncated (``AIFORGE_TRACE_MAX_CHARS``, default 2000) so
  traces stay small; set it to 0 to drop text entirely.
"""

from __future__ import annotations

import functools
import json
import logging
import os
import threading
import time
from collections import deque
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Callable, Deque, Dict, Iterator, List, Optional

_logger = logging.getLogger("aiforge.trace")


def _max_chars() -> int:
    try:
        return int(os.environ.get("AIFORGE_TRACE_MAX_CHARS", "2000"))
    except ValueError:
        return 2000


def _clip(text: Any) -> str:
    limit = _max_chars()
    if limit <= 0:
        return ""
    s = text if isinstance(text, str) else str(text)
    return s if len(s) <= limit else s[:limit] + f"...[+{len(s) - limit} chars]"


def estimate_tokens(text: str) -> int:
    return max(0, round(len(text or "") / 4.0))


class TraceCollector:
    """Thread-safe in-memory event sink plus optional JSONL file sink."""

    def __init__(self, max_events: Optional[int] = None) -> None:
        # Bounded so a long-running API server doesn't grow without limit; the
        # benchmark resets it per task, and the JSONL sink keeps everything.
        limit = max_events or int(os.environ.get("AIFORGE_TRACE_BUFFER", "20000"))
        self._events: Deque[Dict[str, Any]] = deque(maxlen=limit)
        self._lock = threading.Lock()

    def emit(self, event: Dict[str, Any]) -> None:
        event.setdefault("ts", datetime.now(timezone.utc).isoformat())
        with self._lock:
            self._events.append(event)
        path = os.environ.get("AIFORGE_TRACE_FILE")
        if path:
            try:
                os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
                with self._lock, open(path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(event, default=str) + "\n")
            except OSError as exc:  # tracing must never break generation
                _logger.warning("Could not write trace event to %s: %s", path, exc)

    def events(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._events)

    def reset(self) -> None:
        with self._lock:
            self._events.clear()

    def summary(self) -> Dict[str, Any]:
        """Aggregates LLM and node events into the numbers benchmarks report."""
        events = self.events()
        llm = [e for e in events if e.get("kind") == "llm_call"]
        nodes = [e for e in events if e.get("kind") == "node"]

        per_agent: Dict[str, Dict[str, Any]] = {}
        for e in llm:
            a = per_agent.setdefault(e.get("agent", "unknown"), {
                "calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "latency_ms": 0.0,
                "fallbacks": 0, "cache_hits": 0,
            })
            a["calls"] += 1
            a["prompt_tokens"] += int(e.get("prompt_tokens") or 0)
            a["completion_tokens"] += int(e.get("completion_tokens") or 0)
            a["latency_ms"] = round(a["latency_ms"] + float(e.get("latency_ms") or 0.0), 1)
            a["fallbacks"] += 1 if e.get("fallback") else 0
            a["cache_hits"] += 1 if e.get("cache_hit") else 0

        return {
            "llm_calls": len(llm),
            "prompt_tokens": sum(int(e.get("prompt_tokens") or 0) for e in llm),
            "completion_tokens": sum(int(e.get("completion_tokens") or 0) for e in llm),
            "tokens_estimated": any(e.get("tokens_estimated") for e in llm),
            "llm_latency_ms": round(sum(float(e.get("latency_ms") or 0.0) for e in llm), 1),
            "llm_fallbacks": sum(1 for e in llm if e.get("fallback")),
            "llm_cache_hits": sum(1 for e in llm if e.get("cache_hit")),
            "models": sorted({e.get("model") for e in llm if e.get("model")}),
            "node_runs": len(nodes),
            "node_failures": sum(1 for e in nodes if e.get("status") == "error"),
            "per_agent": per_agent,
            "per_node_ms": _sum_by(nodes, "node", "latency_ms"),
        }


def _sum_by(events: List[Dict[str, Any]], key: str, field: str) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for e in events:
        k = e.get(key, "unknown")
        out[k] = round(out.get(k, 0.0) + float(e.get(field) or 0.0), 1)
    return out


global_trace = TraceCollector()


def record_llm_call(
    *,
    agent: str,
    model: str,
    prompt: str,
    output: str,
    latency_ms: float,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    cache_hit: bool = False,
    fallback: bool = False,
    error: Optional[str] = None,
) -> None:
    estimated = prompt_tokens is None or completion_tokens is None
    global_trace.emit({
        "kind": "llm_call",
        "agent": agent,
        "model": model,
        "latency_ms": round(latency_ms, 1),
        "prompt_tokens": prompt_tokens if prompt_tokens is not None else estimate_tokens(prompt),
        "completion_tokens": completion_tokens if completion_tokens is not None else estimate_tokens(output),
        "tokens_estimated": estimated,
        "cache_hit": cache_hit,
        "fallback": fallback,
        "error": error,
        "prompt": _clip(prompt),
        "output": _clip(output),
    })


def token_counts_from_response(response: Any) -> tuple[Optional[int], Optional[int]]:
    """Reads provider-reported token counts from an Ollama chat response."""
    def _get(key: str) -> Optional[int]:
        try:
            val = response[key] if isinstance(response, dict) else getattr(response, key, None)
        except (KeyError, TypeError):
            val = None
        return int(val) if isinstance(val, (int, float)) else None

    return _get("prompt_eval_count"), _get("eval_count")


@contextmanager
def trace_node(name: str) -> Iterator[Dict[str, Any]]:
    """Context manager that emits one ``node`` event with latency and status."""
    info: Dict[str, Any] = {}
    start = time.perf_counter()
    try:
        yield info
    except Exception as exc:
        global_trace.emit({
            "kind": "node", "node": name, "status": "error",
            "latency_ms": round((time.perf_counter() - start) * 1000, 1),
            "error": f"{type(exc).__name__}: {exc}", **info,
        })
        raise
    global_trace.emit({
        "kind": "node", "node": name, "status": "ok",
        "latency_ms": round((time.perf_counter() - start) * 1000, 1), **info,
    })


def traced_node(name: str, fn: Callable[..., Any]) -> Callable[..., Any]:
    """Wraps an async LangGraph node so each invocation is traced."""

    @functools.wraps(fn)
    async def wrapper(state: Any, *args: Any, **kwargs: Any) -> Any:
        with trace_node(name) as info:
            result = await fn(state, *args, **kwargs)
            if isinstance(result, dict) and "status" in result:
                info["state_status"] = str(result.get("status"))
            return result

    return wrapper
