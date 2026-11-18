"""
Search/replace edits (backend/repair/edits.py), repo-aware repair context (backend/repair/context.py) and the memory
of verified fixes (backend/repair/fix_memory.py), and how the repair paths use them.
"""

from backend.repair.context import build_repair_context, error_symbols, imported_files, summarize, symbol_map
from backend.repair.edits import Edit, apply_edits, parse_edits
from backend.repair.fix_memory import FixMemory, error_signature, hint_text

MAIN = '''from fastapi import FastAPI, HTTPException
from backend.models import Note
from backend.store import NOTES

app = FastAPI()


@app.get("/notes/{note_id}")
def get_note(note_id: int):
    return NOTES.get(note_id, {})
'''
MODELS = "from pydantic import BaseModel\n\n\nclass Note(BaseModel):\n    title: str\n    body: str = ''\n"
STORE = "NOTES = {}\n\n\ndef add(note):\n    NOTES[len(NOTES) + 1] = note\n    return len(NOTES)\n"
TEST = "from backend.main import app\n\n\ndef test_missing_note_is_404():\n    assert False\n"
FILES = {"backend/main.py": MAIN, "backend/models.py": MODELS, "backend/store.py": STORE, "tests/test_notes.py": TEST,
         "frontend/src/App.jsx": "export default function App() { return <h1>Notes</h1>; }\n"}


# --- edits ------------------------------------------------------------------------------------------------------

REPLY = '''Here is the fix.

backend/main.py
```python
<<<<<<< SEARCH
def get_note(note_id: int):
    return NOTES.get(note_id, {})
=======
def get_note(note_id: int):
    if note_id not in NOTES:
        raise HTTPException(status_code=404)
    return NOTES[note_id]
>>>>>>> REPLACE
```

`backend/errors.py`
<<<<<<< SEARCH
=======
class NotFound(Exception):
    pass
>>>>>>> REPLACE
'''


def test_edits_are_parsed_with_their_paths_and_applied_precisely():
    edits = parse_edits(REPLY)
    assert [e.path for e in edits] == ["backend/main.py", "backend/errors.py"]
    res = apply_edits(FILES, edits)
    assert res.errors == [] and res.applied == 2
    assert "raise HTTPException(status_code=404)" in res.changed["backend/main.py"]
    assert res.changed["backend/main.py"].startswith(MAIN.split("@app.get")[0]), "the rest of the file is untouched"
    assert res.changed["backend/errors.py"] == "class NotFound(Exception):\n    pass\n"
    assert set(res.changed) == {"backend/main.py", "backend/errors.py"}


def test_an_edit_that_does_not_match_exactly_one_place_is_refused_with_a_reason():
    missing = apply_edits(FILES, [Edit("backend/main.py", "def nowhere():\n    pass", "x")])
    assert missing.changed == {} and "not found" in missing.errors[0]
    twice = apply_edits({"a.py": "x = 1\nx = 1\n"}, [Edit("a.py", "x = 1", "x = 2")])
    assert twice.changed == {} and "2 times" in twice.errors[0]
    unknown = apply_edits(FILES, [Edit("backend/nope.py", "a", "b")])
    assert "no such file" in unknown.errors[0]
    overwrite = apply_edits(FILES, [Edit("backend/store.py", "", "everything replaced")])
    assert "empty SEARCH" in overwrite.errors[0] and overwrite.changed == {}


def test_trailing_whitespace_and_a_uniform_indentation_offset_are_tolerated():
    src = "class A:\n    def f(self):\n        return 1   \n"
    # the model dropped the trailing spaces and the class indentation
    res = apply_edits({"a.py": src}, [Edit("a.py", "def f(self):\n    return 1", "def f(self):\n    return 2")])
    assert res.errors == [] and res.changed["a.py"] == "class A:\n    def f(self):\n        return 2\n"


# --- repair context ---------------------------------------------------------------------------------------------

TRACE = '''Traceback (most recent call last):
  File "/work/proj/backend/main.py", line 10, in get_note
    return NOTES.get(note_id, {})
  File "/usr/lib/python3.11/site-packages/starlette/routing.py", line 1, in x
NameError: name 'Note' is not defined
FAILED tests/test_notes.py::test_missing_note_is_404'''


def test_the_context_follows_the_traceback_the_imports_and_the_symbols_named_in_the_error():
    assert error_symbols(TRACE) == {"Note"}
    assert symbol_map(FILES)["Note"] == ["backend/models.py"] and "add" in symbol_map(FILES)
    assert imported_files("backend/main.py", FILES) == ["backend/models.py", "backend/store.py"]
    ctx = build_repair_context(FILES, TRACE + "\ntests/test_notes.py:5: AssertionError")
    reasons = dict(ctx.files)
    assert ctx.paths[0] == "backend/main.py" and reasons["backend/main.py"] == "in the traceback"
    assert reasons["backend/models.py"] == "defines `Note`"
    assert reasons["backend/store.py"] == "imported by backend/main.py"
    assert "do not change" in reasons["tests/test_notes.py"]
    assert "frontend/src/App.jsx" not in reasons, "files unrelated to the failure are not sent"


def test_files_past_the_budget_are_summarised_as_signatures():
    body = "    x = 0\n" * 25
    big = {**FILES, "backend/store.py": STORE + "\n".join(f"def helper_{i}():\n{body}    return {i}\n" for i in range(20))}
    ctx = build_repair_context(big, TRACE, budget=1200)
    assert ctx.full[0] == "backend/main.py" and "backend/store.py" in ctx.summarized
    assert "def helper_1():" in ctx.text and "return 1\n" not in ctx.text.split("### backend/store.py")[1]
    assert summarize("backend/models.py", MODELS).splitlines() == ["class Note(BaseModel):"]


# --- fix memory -------------------------------------------------------------------------------------------------

def test_error_signatures_ignore_paths_numbers_and_literals():
    a = error_signature('File "/a/b.py"\nFileNotFoundError: [Errno 2] No such file or directory: "/tmp/x.db"')
    b = error_signature("E   FileNotFoundError: [Errno 2] No such file or directory: 'data/notes.sqlite'")
    assert a["type"] == "FileNotFoundError" and a["signature"] == b["signature"]


def test_verified_fixes_are_remembered_per_user_and_suggested_for_similar_errors(tmp_path):
    mem = FixMemory(tmp_path / "fixes.json")
    before = {"backend/db.py": "conn = sqlite3.connect('data/app.db')\n"}
    after = {"backend/db.py": "os.makedirs('data', exist_ok=True)\nconn = sqlite3.connect('data/app.db')\n"}
    err = "sqlite3.OperationalError: unable to open database file 'data/app.db'"
    assert mem.record("alice", "p1", err, "llm_search_replace", before, after, source="debug_loop")
    assert mem.record(None, "p1", err, "x", before, after, source="debug_loop") is None, "no owner: not remembered"
    assert mem.record("bob", "p2", err, "x", before, before, source="debug_loop") is None, "no change: not remembered"

    same = mem.lookup("alice", "E  sqlite3.OperationalError: unable to open database file 'other/place.db'")
    assert len(same) == 1 and same[0]["match"] == 1.0 and "os.makedirs" in same[0]["diff"]
    assert mem.lookup("bob", err) == [], "another user's fixes are never shown"
    assert mem.lookup("alice", "KeyError: 'title'") == [], "a different error type is not a match"
    hint = hint_text(same)
    assert "verified by tests" in hint and "os.makedirs" in hint


# --- the repair paths -------------------------------------------------------------------------------------------

def test_the_debug_loop_repairs_with_edits_and_retries_an_edit_that_did_not_apply(monkeypatch):
    import backend.agents.repair_strategies as rs
    import backend.services.llm as llm
    monkeypatch.setenv("AIFORGE_LLM_REPAIR", "1")
    prompts = []
    replies = iter([
        "backend/main.py\n<<<<<<< SEARCH\ndef get_note(id):\n=======\ndef get_note(id): pass\n>>>>>>> REPLACE",   # wrong
        REPLY.split("`backend/errors.py`")[0],                                                                    # right
    ])

    def model(system, prompt, model=None, task="general"):
        prompts.append(prompt)
        return next(replies)
    monkeypatch.setattr(llm, "generate_text", model)
    strategy, changes = rs.llm_repair(FILES, TRACE, [])
    assert strategy == "llm_search_replace" and set(changes) == {"backend/main.py"}
    assert "raise HTTPException(status_code=404)" in changes["backend/main.py"]
    assert len(prompts) == 2 and "not found" in prompts[1], "the retry says why the first edit failed"
    assert "### backend/models.py" in prompts[0] and "defines `Note`" in prompts[0], "related files are shown"
    assert "frontend/src/App.jsx" not in prompts[0].split("Files involved")[1]


def test_the_debug_loop_never_edits_tests_and_still_accepts_a_whole_file_reply(monkeypatch):
    import backend.agents.repair_strategies as rs
    import backend.services.llm as llm
    monkeypatch.setenv("AIFORGE_LLM_REPAIR", "1")
    test_edit = "tests/test_notes.py\n<<<<<<< SEARCH\n    assert False\n=======\n    assert True\n>>>>>>> REPLACE"
    monkeypatch.setattr(llm, "generate_text", lambda *a, **k: test_edit)
    assert rs.llm_repair(FILES, TRACE, []) == ("none", {})
    fixed = MAIN.replace("return NOTES.get(note_id, {})", "return NOTES[note_id]")
    monkeypatch.setattr(llm, "generate_text", lambda *a, **k: f"```python\n{fixed}```")
    assert rs.llm_repair(FILES, TRACE, []) == ("llm_rewrite_file", {"backend/main.py": fixed})


def test_remembered_fixes_reach_the_repair_prompt(monkeypatch):
    import backend.agents.repair_strategies as rs
    import backend.services.llm as llm
    from backend.repair.fix_memory import global_fix_memory
    monkeypatch.setenv("AIFORGE_LLM_REPAIR", "1")
    global_fix_memory.record("alice", "old", "NameError: name 'Note' is not defined", "llm_search_replace",
                             {"backend/main.py": "x"}, {"backend/main.py": "from backend.models import Note\nx"},
                             source="execution_guardian")
    seen = []
    monkeypatch.setattr(llm, "generate_text", lambda s, p, **k: seen.append(p) or "no edits")
    rs.llm_repair(FILES, TRACE, [], memory_user="alice")
    assert "from backend.models import Note" in seen[0] and "verified by tests" in seen[0]
    seen.clear()
    rs.llm_repair(FILES, TRACE, [], memory_user="bob")
    assert "verified by tests" not in seen[0]


def test_the_project_editor_applies_edits_and_still_reads_whole_files(tmp_path):
    from backend.generation.project_editor import propose_changes
    for rel, src in FILES.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(src, encoding="utf-8")
    sent = []
    changes, rejected = propose_changes(tmp_path, "return 404 for a missing note", FILES, ["backend/main.py"],
                                        generate=lambda s, p: sent.append(p) or REPLY)
    assert set(changes) == {"backend/main.py", "backend/errors.py"} and not rejected
    assert "<<<<<<< SEARCH" in sent[0], "the request asks for edits"
    whole = "### backend/store.py\n```python\nNOTES = {1: 'x'}\n```"
    changes, _ = propose_changes(tmp_path, "seed a note", FILES, ["backend/store.py"], generate=lambda s, p: whole)
    assert changes == {"backend/store.py": "NOTES = {1: 'x'}\n"} or changes == {"backend/store.py": "NOTES = {1: 'x'}"}


# --- where verified fixes are recorded --------------------------------------------------------------------------

def test_a_guardian_repair_verified_by_the_rerun_is_remembered_for_that_user(tmp_path):
    from backend.execution_guardian.service import ExecutionGuardian, VerificationStore
    from backend.repair.fix_memory import global_fix_memory
    from tests.execution_guardian.sample import CALC, CALC_WRONG, file_answer, fixed_agent, python_project
    g = ExecutionGuardian(VerificationStore(tmp_path / "eg"), background=False,
                          generate=fixed_agent(file_answer("calc.py", CALC)), autopilot=None)
    v = g.start("p1", python_project(tmp_path / "p", calc=CALC_WRONG), "u1")
    assert v.repairs and v.repairs[0].outcome == "resolved"
    saved = global_fix_memory._load()
    assert len(saved) == 1 and saved[0]["user_id"] == "u1"
    assert saved[0]["source"] == "execution_guardian" and saved[0]["files"] == ["calc.py"]


def test_a_debug_loop_patch_is_remembered_only_with_an_owner(monkeypatch):
    import backend.graph.parallel_workflow as wf
    from backend.repair.fix_memory import global_fix_memory
    state = {"generation_id": "g1", "project_id": "p1",
             "applied_fix": {"cycle": 1, "files_modified": ["backend/main.py"]},
             "file_backups": {"backend/main.py": MAIN},
             "files": {"backend/main.py": MAIN.replace("from backend.store", "from backend.models import Note\nfrom backend.store")},
             "fixes": [{"error_text": TRACE, "strategy": "llm_search_replace"}]}
    monkeypatch.setattr(wf, "_owner_of", lambda s: None)
    assert wf._record_verified_fix(state) is None
    monkeypatch.setattr(wf, "_owner_of", lambda s: "alice")
    assert wf._record_verified_fix(state)
    match = global_fix_memory.lookup("alice", "NameError: name 'Note' is not defined")
    assert match and match[0]["strategy"] == "llm_search_replace" and "+from backend.models import Note" in match[0]["diff"]


def test_secrets_never_enter_the_fix_memory(tmp_path):
    mem = FixMemory(tmp_path / "fixes.json")
    key = "sk-" + "a1B2c3D4e5F6g7H8i9J0k1L2"
    mem.record("alice", "p1", f"KeyError: 'OPENAI' (api_key={key})", "x",
               {"cfg.py": "x = 1\n"}, {"cfg.py": f"x = 1\nAPI_KEY = '{key}'\n"}, source="debug_loop")
    stored = (tmp_path / "fixes.json").read_text(encoding="utf-8")
    assert key not in stored and "REDACTED" in stored
