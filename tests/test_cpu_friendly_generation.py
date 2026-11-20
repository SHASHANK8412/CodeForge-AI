"""
Builds on a CPU-only machine: local model calls take turns (and the clock starts when a call runs), long answers get the
long ceiling; interface mismatches between generated modules are repaired; a repair is judged on the code-quality gate
as well as the tests.
"""

import asyncio
import threading
import time

import pytest

from backend.agents import repair_strategies as rs
from backend.execution import repair_policy as rp
from backend.services import llm


# --- 1. local model calls take turns ----------------------------------------------------------------------------

@pytest.fixture
def fake_ollama(monkeypatch):
    state = {"running": 0, "max": 0, "calls": 0}

    async def chat(model, messages, stream=False, options=None):
        state["running"] += 1
        state["max"] = max(state["max"], state["running"])
        state["calls"] += 1
        await asyncio.sleep(0.3)
        state["running"] -= 1
        return {"message": {"content": "ok"}, "prompt_eval_count": 5, "eval_count": 2}

    monkeypatch.setattr(llm, "_chat_completion_async", chat)
    monkeypatch.setattr(llm, "_get_cached_response", lambda key: None)
    monkeypatch.setattr(llm, "_set_cached_response", lambda key, value: None)
    monkeypatch.setattr(llm, "_LOCAL_SLOTS", threading.BoundedSemaphore(1))
    return state


def test_parallel_agents_take_turns_on_the_local_model(fake_ollama):
    async def three_agents():
        return await asyncio.gather(*(llm.generate_text_async("", f"write the {a}", task=a)
                                      for a in ("frontend", "backend", "database")))
    assert asyncio.run(three_agents()) == ["ok", "ok", "ok"]
    assert fake_ollama["calls"] == 3 and fake_ollama["max"] == 1, "one call at a time instead of splitting the CPU"


def test_the_deadline_starts_when_a_call_runs_not_while_it_waits(fake_ollama, monkeypatch):
    """Each call takes 0.3 s and the limit is 0.5 s; three in a row take 0.9 s, and none times out waiting."""
    monkeypatch.setattr(llm, "LLM_TIMEOUT_SECONDS", 0.5)
    monkeypatch.setattr(llm, "LLM_LONG_TIMEOUT_SECONDS", 0.5)

    async def three():
        return await asyncio.gather(*(llm.generate_text_async("", f"q{i}", task="general") for i in range(3)))
    started = time.time()
    assert asyncio.run(three()) == ["ok"] * 3
    assert time.time() - started >= 0.85


def test_long_answers_get_the_long_ceiling(monkeypatch):
    monkeypatch.setattr(llm, "LLM_TIMEOUT_SECONDS", 900.0)
    monkeypatch.setattr(llm, "LLM_LONG_TIMEOUT_SECONDS", 1800.0)
    assert llm.call_timeout({"num_predict": 2500}) == 1800.0, "a whole source file (CODING profile)"
    assert llm.call_timeout({"num_predict": 2800}) == 1800.0, "an architecture plan"
    assert llm.call_timeout({"num_predict": 1500}) == 900.0 and llm.call_timeout(None) == 900.0


# --- 2. interface mismatches between generated modules ------------------------------------------------------------

DATABASE = '''from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///./app.db")
SessionLocal = sessionmaker(bind=engine)
'''
MAIN = '''from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session
from backend.database import engine, get_db

app = FastAPI()


def get_db():
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()


@app.get("/notes")
def notes(db: Session = Depends(get_db)):
    return []
'''
TEST = "from backend.database import get_db\nfrom backend.main import app\n\n\ndef test_x():\n    assert app\n"


def _missing(file, name="get_db"):
    return {"file": file, "line": 3, "code": "AIF-missing-name",
            "message": f"`{name}` is not defined in local module `backend.database` (backend/database.py)"}


def test_a_name_the_tests_import_from_a_module_is_moved_there_with_its_imports():
    files = {"backend/database.py": DATABASE, "backend/main.py": MAIN, "tests/test_notes.py": TEST}
    out = rs.fix_missing_local_names(files, [_missing("backend/main.py"), _missing("tests/test_notes.py")])
    assert set(out) == {"backend/database.py", "backend/main.py"}, "tests are never edited"
    assert "def get_db():" in out["backend/database.py"] and "from sqlalchemy.orm import Session" in out["backend/database.py"]
    assert "def get_db" not in out["backend/main.py"]
    assert "from backend.database import engine, get_db" in out["backend/main.py"], "main.py keeps importing it"


def test_without_tests_needing_it_the_bad_import_is_dropped():
    files = {"backend/database.py": DATABASE, "backend/main.py": MAIN}
    out = rs.fix_missing_local_names(files, [_missing("backend/main.py")])
    assert out == {"backend/main.py": MAIN.replace("from backend.database import engine, get_db",
                                                    "from backend.database import engine")}


def test_a_name_defined_in_another_module_is_imported_from_there():
    files = {"backend/database.py": DATABASE, "backend/deps.py": "def get_db():\n    return None\n",
             "backend/routes.py": "from backend.database import get_db\n\n\ndef r():\n    return get_db()\n"}
    out = rs.fix_missing_local_names(files, [_missing("backend/routes.py")])
    assert out == {"backend/routes.py": "from backend.deps import get_db\n\n\ndef r():\n    return get_db()\n"}


def test_the_model_repair_is_told_where_the_tests_expect_the_name(monkeypatch):
    import backend.services.llm as service
    monkeypatch.setenv("AIFORGE_LLM_REPAIR", "1")
    seen = []
    monkeypatch.setattr(service, "generate_text", lambda s, p, **k: seen.append(p) or "no edits")
    files = {"backend/database.py": DATABASE, "backend/main.py": MAIN.replace("def get_db", "def other_db"),
             "tests/test_notes.py": TEST}
    rs.llm_repair(files, "", [_missing("backend/main.py"), _missing("tests/test_notes.py")])
    assert "Interface mismatches" in seen[0] and "the tests import it from there" in seen[0]
    assert "### backend/database.py" in seen[0], "the module the name belongs in is shown"


# --- judged on the code-quality gate too ---------------------------------------------------------------------------

def test_fewer_blocking_issues_with_the_same_first_error_is_progress():
    """Seen in the benchmark: two bugs in main.py; the import repair fixed one, the first error shown stayed the same."""
    base = {"exit_code": 1, "passing": [], "failing": ["t::a"], "outcomes": {"t::a": "error"},
            "error_line": "E   ImportError: cannot import name 'get_db'"}
    assert rp.judge_attempt({**base, "blocking": 2}, {**base, "blocking": 1})["verdict"] == "improved"
    assert rp.judge_attempt({**base, "blocking": 1}, {**base, "blocking": 1})["verdict"] == "no_effect"
    assert rp.judge_attempt({**base, "blocking": None}, {**base, "blocking": 0})["verdict"] == "no_effect", \
        "no gate evidence before: not counted"
