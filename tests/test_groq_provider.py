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
    assert sent["model"] == "openai/gpt-oss-120b" and sent["messages"][0]["role"] == "system"
    assert sent["max_completion_tokens"] >= groq.MIN_COMPLETION_TOKENS and sent["reasoning_effort"] == "medium"


def test_other_tasks_stay_on_the_local_model(groq_on, monkeypatch):
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
    monkeypatch.setenv("AIFORGE_GROQ_MODEL", "qwen/qwen3-32b")
    monkeypatch.setenv("AIFORGE_GROQ_TASKS", "backend, frontend")
    assert groq.handles("frontend") and not groq.handles("architect")
    status = groq.status()
    assert status == {"enabled": True, "model": "qwen/qwen3-32b", "tasks": ["backend", "frontend"]}
    assert KEY not in json.dumps(status)
    assert "reasoning_effort" not in groq._payload([], {})
