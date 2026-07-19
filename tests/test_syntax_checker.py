import pytest
from pathlib import Path
from backend.validation.syntax_checker import SyntaxChecker


def test_syntax_checker_valid_python(tmp_path):
    checker = SyntaxChecker()
    (tmp_path / "backend").mkdir()
    
    # Create a valid Python file
    (tmp_path / "backend/valid.py").write_text("""def hello():
    print("Hello")
""")

    res = checker.validate(tmp_path)
    assert res.status == "PASS"
    assert res.score == 100.0
    assert len(res.errors) == 0
    assert res.metadata["files_checked"] == 1


def test_syntax_checker_invalid_python(tmp_path):
    checker = SyntaxChecker()
    (tmp_path / "backend").mkdir()

    # Create an invalid Python file
    (tmp_path / "backend/invalid.py").write_text("""def hello(
    print("Hello")
""")

    res = checker.validate(tmp_path)
    assert res.status == "FAIL"
    assert res.score == 0.0
    assert any("Syntax error" in err for err in res.errors)
