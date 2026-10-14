"""
Regressions from a real generation (qwen2.5-coder, Bookmark Saver):
- `from backend.database import engine, Session`: Session is SQLAlchemy's, not the module's
- the project folder was "Project_Name_Bookmark_Saver" from a "Project name: ..." prompt
"""
from backend.agents.planner_agent import project_name_from_prompt
from backend.agents.repair_strategies import fix_misplaced_imports, propose_repairs

DATABASE = "from sqlalchemy.orm import sessionmaker\nengine = None\nSessionLocal = sessionmaker()\n"
MAIN = "from fastapi import FastAPI\nfrom backend.database import engine, Session\n\napp = FastAPI()\n"
ERRORS = [{"file": "backend/main.py", "line": 2, "code": "AIF-missing-name",
           "message": "`Session` is not defined in local module `backend.database` (backend/database.py)"}]


def test_library_name_is_imported_from_the_library():
    fixed = fix_misplaced_imports({"backend/main.py": MAIN, "backend/database.py": DATABASE}, ERRORS)["backend/main.py"]
    assert "from backend.database import engine\n" in fixed
    assert "from sqlalchemy.orm import Session" in fixed
    compile(fixed, "main.py", "exec")


def test_only_name_on_the_line_removes_the_line_and_unknown_names_are_left_alone():
    files = {"backend/main.py": "from backend.database import Session\nx = 1\n"}
    errors = [dict(ERRORS[0], line=1)]
    assert fix_misplaced_imports(files, errors)["backend/main.py"].splitlines() == ["from sqlalchemy.orm import Session", "x = 1"]
    unknown = [dict(ERRORS[0], message="`get_widget` is not defined in local module `backend.database` (x)")]
    assert fix_misplaced_imports({"backend/main.py": MAIN}, unknown) == {}


def test_propose_repairs_uses_it():
    name, changes = propose_repairs({"backend/main.py": MAIN, "backend/database.py": DATABASE}, "", ERRORS)
    assert name == "fix_misplaced_imports" and "backend/main.py" in changes


def test_project_name_prefix_is_understood():
    assert project_name_from_prompt("Project name: Bookmark Saver. Users can save bookmarks.") == "Bookmark Saver"
    assert project_name_from_prompt("project name: CRM API\nBuild a CRM") == "CRM API"
    assert project_name_from_prompt("Build a recipe box where users add recipes") != ""
