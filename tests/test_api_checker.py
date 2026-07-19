import pytest
from pathlib import Path
from backend.validation.api_checker import APIChecker


def test_api_checker_valid_route(tmp_path):
    checker = APIChecker()
    (tmp_path / "backend").mkdir()

    # Valid route
    (tmp_path / "backend/routes.py").write_text("""@app.get("/users", response_model=List[User], status_code=200)
def users():
    try:
        return {"users":[]}
    except Exception:
        pass
""")

    res = checker.validate(tmp_path)
    assert res.score == 100.0
    assert len(res.errors) == 0
    assert res.metadata["routes_scanned"] == 1


def test_api_checker_broken_route(tmp_path):
    checker = APIChecker()
    (tmp_path / "backend").mkdir()

    # Route lacking response_model, status_code, and error try-except block
    (tmp_path / "backend/routes.py").write_text("""@app.get("/users")
def users():
    pass
""")

    res = checker.validate(tmp_path)
    # Check warning detection
    assert len(res.warnings) > 0
    assert any("response_model" in warn for warn in res.warnings)
    assert any("status_code" in warn for warn in res.warnings)
    assert any("error handling" in warn for warn in res.warnings)
