import asyncio

import pytest

import backend.services.llm as llm
from backend.utils.retry import LLMDeadlineExceeded


class _NotFound(Exception):
    status_code = 404


@pytest.fixture(autouse=True)
def _clean_blacklist():
    llm._unavailable_models.clear()
    yield
    llm._unavailable_models.clear()


def test_missing_model_is_detected_but_timeouts_are_not():
    assert llm._is_missing_model_error(_NotFound("model 'x' not found"))
    assert not llm._is_missing_model_error(TimeoutError("timed out"))
    assert not llm._is_missing_model_error(ConnectionError("connection refused"))
    # The old heuristic blacklisted any error mentioning "model".
    assert not llm._is_missing_model_error(RuntimeError("model is busy, try again"))


def test_slow_model_raises_deadline_without_blacklisting(monkeypatch):
    calls = []

    async def slow_completion(model, messages, stream=False, options=None):
        calls.append(model)
        await asyncio.sleep(5)

    monkeypatch.setattr(llm, "_chat_completion_async", slow_completion)
    monkeypatch.setattr(llm, "LLM_TIMEOUT_SECONDS", 0.05)

    with pytest.raises(LLMDeadlineExceeded):
        asyncio.run(llm._chat_completion_with_fallback_async([], "llama3.2:3b"))

    assert calls == ["llama3.2:3b"], "a deadline must not be retried or cascade through fallbacks"
    assert "llama3.2:3b" not in llm._unavailable_models


def test_missing_model_falls_back_to_next_candidate(monkeypatch):
    async def completion(model, messages, stream=False, options=None):
        if model == "ghost-model:latest":
            raise _NotFound("model 'ghost-model:latest' not found")
        return {"message": {"content": f"ok from {model}"}}

    monkeypatch.setattr(llm, "_chat_completion_async", completion)

    result = asyncio.run(llm._chat_completion_with_fallback_async([], "ghost-model:latest"))

    assert result["message"]["content"] == f"ok from {llm.DEFAULT_OLLAMA_MODEL}"
    assert "ghost-model:latest" in llm._unavailable_models


# --- No stand-in output: a failed model call raises; it never returns canned text -------------------------------

TASKS = ("planner", "architect", "frontend", "backend", "database", "testing", "reviewer", "general")


def _down(monkeypatch, error=ConnectionError("connection refused")):
    async def down_async(model, messages, stream=False, options=None):
        raise error

    def down(model, messages, stream=False, options=None):
        raise error

    monkeypatch.setattr(llm, "_chat_completion_async", down_async)
    monkeypatch.setattr(llm, "_chat_completion", down)
    llm.llm_cache.clear()


@pytest.mark.parametrize("task", TASKS)
def test_failed_call_raises_and_caches_nothing(monkeypatch, task):
    _down(monkeypatch)
    prompt = f"Build a notes board ({task})"

    with pytest.raises(llm.LLMUnavailableError) as sync_err:
        llm.generate_text("system", prompt, task=task)
    with pytest.raises(llm.LLMUnavailableError) as async_err:
        asyncio.run(llm.generate_text_async("system", prompt, task=task))

    for err in (sync_err.value, async_err.value):
        assert err.task == task and "ConnectionError" in err.reason
        assert isinstance(err.__cause__, ConnectionError)
    assert llm.llm_cache.get_stats()["current_size"] == 0, "a failure is never cached as an answer"
    assert not hasattr(llm, "_get_structured_task_fallback")


def test_timeout_raises_unavailable(monkeypatch):
    async def slow(model, messages, stream=False, options=None):
        await asyncio.sleep(5)

    monkeypatch.setattr(llm, "_chat_completion_async", slow)
    monkeypatch.setattr(llm, "LLM_TIMEOUT_SECONDS", 0.05)
    llm.llm_cache.clear()

    with pytest.raises(llm.LLMUnavailableError) as err:
        asyncio.run(llm.generate_text_async("system", "Build a notes board", task="backend"))
    assert isinstance(err.value.__cause__, LLMDeadlineExceeded)


def test_streamed_failure_raises_unavailable(monkeypatch):
    _down(monkeypatch)
    token = llm.stream_queue_var.set(asyncio.Queue())
    try:
        with pytest.raises(llm.LLMUnavailableError):
            asyncio.run(llm.generate_text_async("system", "Build a notes board", task="frontend"))
    finally:
        llm.stream_queue_var.reset(token)


@pytest.mark.parametrize("content", ["", "   \n"])
def test_empty_response_is_a_failure(monkeypatch, content):
    async def empty_async(model, messages, stream=False, options=None):
        return {"message": {"content": content}}

    monkeypatch.setattr(llm, "_chat_completion_async", empty_async)
    monkeypatch.setattr(llm, "_chat_completion", lambda model, messages, stream=False, options=None: {"message": {"content": content}})
    llm.llm_cache.clear()

    with pytest.raises(llm.LLMUnavailableError, match="empty response"):
        llm.generate_text("system", "Build a notes board", task="backend")
    with pytest.raises(llm.LLMUnavailableError, match="empty response"):
        asyncio.run(llm.generate_text_async("system", "Build a notes board", task="backend"))
    assert llm.llm_cache.get_stats()["current_size"] == 0


def test_model_fallback_chain_still_answers(monkeypatch):
    """A missing model still falls through to the next real model; only canned text is gone."""
    async def completion(model, messages, stream=False, options=None):
        if model == "ghost-model:latest":
            raise _NotFound("model 'ghost-model:latest' not found")
        return {"message": {"content": f"real answer from {model}"}}

    monkeypatch.setattr(llm, "_chat_completion_async", completion)
    llm.llm_cache.clear()

    reply = asyncio.run(llm.generate_text_async("system", "Build a notes board", model="ghost-model:latest", task="backend"))
    assert reply == f"real answer from {llm.DEFAULT_OLLAMA_MODEL}"
