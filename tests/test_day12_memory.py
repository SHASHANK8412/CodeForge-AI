"""
Day 12: conversation memory.

Originally written against an old MemoryManager API (save_interaction / get_history / get_project /
clear_session) and the removed router graph. Conversation memory now lives in ConversationManager
(SQLite), and the generation pipeline reads it through the context manager. These tests use a
temporary database, so they never touch the real conversation store.
"""
import pytest

from backend.memory.conversation_manager import ConversationManager
from backend.memory.crud import ConversationRepository
from backend.memory.database import ConversationDatabase

from tests._pipeline_doubles import PipelineDoubles


@pytest.fixture
def conversations(tmp_path, monkeypatch):
    manager = ConversationManager(ConversationRepository(ConversationDatabase(tmp_path / "conversations.db")))
    from backend.services import generation_service as gs
    monkeypatch.setattr(gs.global_context_manager, "conv_mgr", manager)
    return manager


def test_memory_manager_conversation_and_project_storage(conversations):
    conversations.record_turn(
        conversation_id="session-a",
        user_prompt="Create login page",
        assistant_response="Use React form components",
        metadata={"intent": "CODING", "agent": "CodingAgent", "plan": "Plan A", "architecture": "Arch A"},
    )

    messages = conversations.get_messages("session-a")
    assert [(m.role, m.content) for m in messages] == [
        ("user", "Create login page"),
        ("assistant", "Use React form components"),
    ]
    assistant = messages[1].metadata
    assert assistant["plan"] == "Plan A"
    assert assistant["architecture"] == "Arch A"
    assert assistant["agent"] == "CodingAgent"
    assert conversations.get_conversation("session-a").message_count == 2


def test_clear_session_removes_all_memory(conversations):
    conversations.record_turn("session-b", "Create FastAPI backend", "Backend ready", {"intent": "CODING"})
    conversations.delete_conversation("session-b")

    assert conversations.get_messages("session-b") == []
    assert conversations.get_conversation("session-b") is None


def test_graph_carries_memory_forward_between_prompts(conversations, monkeypatch):
    doubles = PipelineDoubles(monkeypatch)
    conversations.record_turn(
        "session-c",
        "Write a Python function to validate a login form",
        "```python\ndef validate(user, password):\n    return bool(user and password)\n```",
        {"intent": "CODING", "agent": "CodingAgent"},
    )

    second = doubles.run("Continue", conversation_id="session-c")

    assert second.intent == "CODING", "a bare 'Continue' carries on the previous coding turn"
    assert "coding" in doubles.calls
    prompt = doubles.prompts["coding"][0]
    assert "Write a Python function to validate a login form" in prompt
    assert "def validate(user, password)" in prompt
    assert prompt.rstrip().endswith("Continue")


def test_router_uses_memory_context_for_continuation_hint(conversations):
    from backend.agents.router_agent import global_router_agent
    from backend.services import generation_service as gs

    conversations.record_turn("session-d", "Write a function that parses dates", "```python\ndef parse(s): ...\n```",
                              {"intent": "CODING"})
    ctx = gs.global_context_manager.get_context("session-d", "Continue")
    assert ctx.is_follow_up
    assert global_router_agent.classify_intent("Continue", context_result=ctx)["intent"] == "CODING"

    ctx = gs.global_context_manager.get_context("session-d", "Fix previous bug")
    assert global_router_agent.classify_intent("Fix previous bug", context_result=ctx)["intent"] == "DEBUGGING"

    # Without history there is nothing to continue: the request needs clarification.
    no_history = gs.global_context_manager.get_context("session-empty", "Continue")
    assert no_history.is_follow_up is False
