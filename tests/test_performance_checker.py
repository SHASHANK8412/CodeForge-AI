import pytest
from pathlib import Path
from backend.validation.performance_checker import PerformanceChecker


def test_performance_checker_execution_stats(tmp_path):
    checker = PerformanceChecker()
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend/app.py").write_text("# simple code file")

    res = checker.validate(tmp_path)
    
    assert res.status == "PASS"
    assert res.score == 100.0
    assert "memory_mb" in res.metadata
    assert "cpu_percent" in res.metadata
    assert "total_files" in res.metadata
    assert "total_loc" in res.metadata
