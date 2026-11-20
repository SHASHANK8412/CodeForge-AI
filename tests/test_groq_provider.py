"""
Groq for the coding agents (backend/services/groq_provider.py and its use in backend/services/llm.py).

Groq's HTTP API is replaced by an httpx mock transport; no request leaves the machine.
"""

import asyncio
import json
import logging

import httpx
import pytest

import backend.services.groq_provider as groq
import backend.services.llm as llm

KEY = "gsk_test_key_never_logged"


def _reply(content="def add(a, b):\n    return a + b\n", status=200, model="openai/gpt-oss-120b"):
    def handler(request: httpx.Request) -> httpx.Response:
        handler.requests.append(request)
        if status != 200:
            return httpx.Response(status, json={"error": {"message": "rate limit reached"}})
        return httpx.Response(200, json={"model": model, "choices": [{"message": {"content": content}, "finish_reason": "stop"}],
                                         "usage": {"prompt_tokens": 120, "completion_tokens": 40}})
    handler.requests = []
    return handler


@pytest.fixture
def groq_on(monkeypatch, tmp_path):
    monkeypatch.setenv("GROQ_API_KEY", KEY)
    for var in ("AIFORGE_GROQ_MODEL", "AIFORGE_GROQ_TASKS", "AIFORGE_GROQ_REASONING_EFFORT"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(llm, "_get_cached_response", lambda key: None)
    monkeypatch.setattr(llm, "_set_cached_response", lambda key, value: None)


def _route(monkeypatch, handler):
    """Send groq_provider's HTTP calls to the mock handler."""
    real_sync, real_async = groq.chat, groq.chat_async
    monkeypatch.setattr(groq, "chat", lambda m, o=None: real_sync(m, o, transport=httpx.MockTransport(handler)))

    async def chat_async(m, o=None):
        return await real_async(m, o, transport=httpx.MockTransport(handler))
    monkeypatch.setattr(groq, "chat_async", chat_async)


def _local(monkeypatch, answer="LOCAL ANSWER"):
    calls = []

    def sync(messages, model, stream=False, options=None):
        calls.append(model)
        return {"message": {"content": answer}}

    async def run_async(messages, model, stream=False, options=None):
        calls.append(model)
        return {"message": {"content": answer}}
    monkeypatch.setattr(llm, "_chat_completion_with_fallback", sync)
    monkeypatch.setattr(llm, "_chat_completion_with_fallback_async", run_async)
    return calls


def test_coding_agents_are_answered_by_groq(groq_on, monkeypatch):
    handler = _reply()
    _route(monkeypatch, handler)
    local = _local(monkeypatch)
    assert llm.generate_text("You write code.", "add two numbers", task="backend").startswith("def add")
    assert asyncio.run(llm.generate_text_async("You write code.", "add two numbers", task="architect")).startswith("def add")
    assert local == [], "the local model is not called when Groq answers"
    sent = json.loads(handler.requests[0].content)
    assert handler.requests[0].url == groq.GROQ_CHAT_URL
    assert handler.requests[0].headers["Authorization"] == f"Bearer {KEY}"
    assert sent["model"] == "qwen/qwen3.8-27b" and sent["messages"][0]["role"] == "system"
    assert sent["max_completion_tokens"] >= groq.MIN_COMPLETION_TOKENS
    assert sent["reasoning_format"] == "hidden" and sent["reasoning_effort"] == "default"


def test_every_feature_uses_groq_by_default(groq_on, monkeypatch):
    handler = _reply(content="ok")
    _route(monkeypatch, handler)
    local = _local(monkeypatch)
    for task in ("planner", "documentation", "reviewer", "general", "explanation"):
        assert llm.generate_text("", "do it", task=task) == "ok", task
    assert local == [] and len(handler.requests) == 5
    assert groq.status()["tasks"] == ["all"]


def test_qwen_thinking_never_reaches_the_code(groq_on, monkeypatch):
    _route(monkeypatch, _reply(content="<think>first I consider...</think>\ndef add(a, b):\n    return a + b\n"))
    _local(monkeypatch)
    assert llm.generate_text("", "add", task="backend") == "def add(a, b):\n    return a + b"


def test_gpt_oss_keeps_its_own_reasoning_setting(groq_on, monkeypatch):
    monkeypatch.setenv("AIFORGE_GROQ_MODEL", "openai/gpt-oss-120b")
    body = groq._payload([], {})
    assert body["reasoning_effort"] == "medium" and "reasoning_format" not in body


def test_tasks_not_listed_stay_on_the_local_model(groq_on, monkeypatch):
    monkeypatch.setenv("AIFORGE_GROQ_TASKS", "backend,frontend")
    handler = _reply()
    _route(monkeypatch, handler)
    local = _local(monkeypatch)
    assert llm.generate_text("", "plan it", task="planner") == "LOCAL ANSWER"
    assert asyncio.run(llm.generate_text_async("", "write the docs", task="documentation")) == "LOCAL ANSWER"
    assert handler.requests == [] and len(local) == 2


def test_without_a_key_nothing_is_sent_to_groq(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setattr(groq, "_ENV_FILE", groq._ENV_FILE.parent / "no-such-dir" / ".env")
    assert groq.handles("backend") is False
    assert groq.status() == {"enabled": False, "model": None, "tasks": []}


def test_a_groq_failure_falls_back_to_the_local_model_and_never_logs_the_key(groq_on, monkeypatch, caplog):
    monkeypatch.setenv("AIFORGE_GROQ_RATE_LIMIT_WAIT", "0")      # no waiting: fall back at once
    _route(monkeypatch, _reply(status=429))
    local = _local(monkeypatch)
    with caplog.at_level(logging.WARNING, logger="aiforge.performance"):
        assert asyncio.run(llm.generate_text_async("", "fix the bug", task="debug")) == "LOCAL ANSWER"
    assert len(local) == 1
    assert "rate limit reached" in caplog.text and "using the local model" in caplog.text
    assert KEY not in caplog.text


def test_an_empty_groq_answer_is_a_failure_not_an_answer(groq_on, monkeypatch):
    _route(monkeypatch, _reply(content=""))
    local = _local(monkeypatch)
    assert llm.generate_text("", "write code", task="frontend") == "LOCAL ANSWER" and len(local) == 1


def test_network_errors_become_groq_errors(groq_on):
    def boom(request):
        raise httpx.ConnectError("no route")
    with pytest.raises(groq.GroqError) as exc:
        groq.chat([{"role": "user", "content": "x"}], transport=httpx.MockTransport(boom))
    assert KEY not in str(exc.value)


def test_model_and_tasks_are_configurable(groq_on, monkeypatch):
    monkeypatch.setenv("AIFORGE_GROQ_MODEL", "llama-3.3-70b-versatile")
    monkeypatch.setenv("AIFORGE_GROQ_TASKS", "backend, frontend")
    assert groq.handles("frontend") and not groq.handles("architect")
    status = groq.status()
    assert status == {"enabled": True, "model": "llama-3.3-70b-versatile", "tasks": ["backend", "frontend"]}
    assert KEY not in json.dumps(status)
    assert "reasoning_effort" not in groq._payload([], {})        # not a reasoning model: no reasoning settings


def _limited_then_ok(limited_times, message="Rate limit reached ... Please try again in 1.5s. Need more tokens?"):
    state = {"n": 0}

    def handler(request):
        state["n"] += 1
        if state["n"] <= limited_times:
            return httpx.Response(429, json={"error": {"message": message}})
        return httpx.Response(200, json={"model": "openai/gpt-oss-120b", "choices": [{"message": {"content": "ok code"}}],
                                         "usage": {"prompt_tokens": 1, "completion_tokens": 1}})
    return handler, state


def test_a_rate_limited_call_waits_as_asked_and_retries(groq_on, monkeypatch):
    """Groq's per-minute token limit (8,000 on the on-demand tier) made calls fall back to the local model at once."""
    handler, state = _limited_then_ok(2)
    waits = []
    res = groq.chat([{"role": "user", "content": "x"}], transport=httpx.MockTransport(handler), sleep=waits.append)
    assert res.content == "ok code" and state["n"] == 3
    assert waits == [1.75, 1.75], "the wait Groq asked for (1.5 s) plus a small margin"

    async_waits = []

    async def record(seconds):
        async_waits.append(seconds)
    monkeypatch.setenv("AIFORGE_GROQ_RATE_LIMIT_WAIT", "120")      # a 62.75 s wait fits a 120 s budget
    handler, state = _limited_then_ok(1, "Please try again in 1m2.5s.")
    res = asyncio.run(groq.chat_async([{"role": "user", "content": "x"}], transport=httpx.MockTransport(handler), sleep=record))
    assert res.content == "ok code" and async_waits == [62.75]


def test_the_rate_limit_wait_is_bounded(groq_on, monkeypatch):
    monkeypatch.setenv("AIFORGE_GROQ_RATE_LIMIT_WAIT", "4")
    handler, state = _limited_then_ok(99)
    waits = []
    with pytest.raises(groq.GroqRateLimited):
        groq.chat([{"role": "user", "content": "x"}], transport=httpx.MockTransport(handler), sleep=waits.append)
    # 1.75 + 1.75 = 3.5 s fits the 4 s budget; a third wait would not: give up and fall back
    assert waits == [1.75, 1.75] and state["n"] == 3
