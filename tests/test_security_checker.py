import pytest
from pathlib import Path
from backend.validation.security_checker import SecurityChecker


def test_security_checker_hardcoded_secret(tmp_path):
    checker = SecurityChecker()
    (tmp_path / "backend").mkdir()

    (tmp_path / "backend/config.py").write_text("""
API_KEY = "123456789abcdef"
""")

    res = checker.validate(tmp_path)
    assert any("Hardcoded Secret" in err for err in res.errors)
    assert any(issue["severity"] == "critical" or issue["severity"] == "high" for issue in res.metadata["issues"])


def test_security_checker_unsafe_eval(tmp_path):
    checker = SecurityChecker()
    (tmp_path / "backend").mkdir()

    (tmp_path / "backend/app.py").write_text("""
eval(user_input)
""")

    res = checker.validate(tmp_path)
    assert any("Unsafe Execution" in err for err in res.errors)
