import pytest
from pathlib import Path
from backend.validation.dependency_checker import DependencyChecker


def test_dependency_checker_missing_dep(tmp_path):
    checker = DependencyChecker()

    (tmp_path / "backend").mkdir()
    
    # Create requirements.txt
    (tmp_path / "backend/requirements.txt").write_text("""fastapi
uvicorn
""")

    # Create python file with imported library not in requirements
    (tmp_path / "backend/main.py").write_text("""import fastapi
import requests
""")

    res = checker.validate(tmp_path)
    
    # Verify missing dependency
    assert any("requests" in err for err in res.errors)
    assert any("requests" in sugg for sugg in res.metadata["suggestions"])
