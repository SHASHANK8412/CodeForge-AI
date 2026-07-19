import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from backend.validation.models import ValidationResult
from backend.validation.syntax_checker import SyntaxChecker
from backend.validation.dependency_checker import DependencyChecker
from backend.validation.api_checker import APIChecker
from backend.validation.frontend_checker import FrontendChecker
from backend.validation.database_checker import DatabaseChecker
from backend.validation.security_checker import SecurityChecker
from backend.validation.performance_checker import PerformanceChecker
from backend.validation.quality_score import QualityScoreCalculator
from backend.validation.validator import ValidationOrchestrator


def test_syntax_checker_valid_and_invalid(tmp_path):
    checker = SyntaxChecker()

    # Create directories
    (tmp_path / "backend").mkdir()
    
    # 1. Valid Python
    (tmp_path / "backend/valid.py").write_text("""
def add_nums(a, b):
    return a + b
""")

    # 2. Invalid Python (Syntax error)
    (tmp_path / "backend/invalid.py").write_text("""
def add_nums(a, b)
    return a + b
""")

    res = checker.validate(tmp_path)
    assert res.score < 100.0
    assert any("Syntax error" in err for err in res.errors)
    assert res.metadata["files_checked"] == 2
    assert res.metadata["files_failed"] == 1


def test_dependency_checker_missing_and_duplicates(tmp_path):
    checker = DependencyChecker()

    (tmp_path / "backend").mkdir()
    (tmp_path / "frontend").mkdir()

    # requirements.txt
    (tmp_path / "backend/requirements.txt").write_text("""
fastapi>=0.95.0
fastapi
""")

    # py files importing standard and non-standard packages
    (tmp_path / "backend/main.py").write_text("""
import os
import fastapi
import sqlalchemy
""")

    res = checker.validate(tmp_path)
    assert any("Duplicate dependency" in err for err in res.errors)
    assert any("Missing dependency" in err for err in res.errors) # sqlalchemy is missing in requirements.txt
    assert any("fastapi" in sugg for sugg in res.metadata["suggestions"])


def test_api_checker_duplicates_and_missing_response(tmp_path):
    checker = APIChecker()

    (tmp_path / "backend").mkdir()
    (tmp_path / "backend/main.py").write_text("""
from fastapi import FastAPI, Depends
app = FastAPI()

@app.get("/users")
def get_users():
    return []

@app.get("/users")
def get_users_dup():
    return []
""")

    res = checker.validate(tmp_path)
    assert any("Duplicate API route" in err for err in res.errors)
    assert any("Missing response_model" in warn for warn in res.warnings)


def test_frontend_checker_broken_imports_and_hooks(tmp_path):
    checker = FrontendChecker()

    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend/App.jsx").write_text("""
import React from 'react';
import Card from './components/Card';

function App() {
    if (true) {
        React.useState(0);
    }
    return <div />;
}
""")

    res = checker.validate(tmp_path)
    assert any("Broken import reference" in err for err in res.errors)
    assert any("Invalid hook call" in err for err in res.errors)


def test_database_checker_convention_and_keys(tmp_path):
    checker = DatabaseChecker()

    (tmp_path / "backend").mkdir()
    
    # Class name does not follow CamelCase (bad_model)
    # Model table name is not lower snake_case (UsersTable)
    # Missing primary key Column
    (tmp_path / "backend/models.py").write_text("""
from sqlalchemy import Column, String
class bad_model(Base):
    __tablename__ = "UsersTable"
    name = Column(String)
""")

    res = checker.validate(tmp_path)
    assert any("no primary_key defined" in err for err in res.errors)
    assert any("naming convention" in warn for warn in res.warnings)
    assert any("lower snake_case" in warn for warn in res.warnings)


def test_security_checker_vulnerabilities(tmp_path):
    checker = SecurityChecker()

    (tmp_path / "backend").mkdir()
    (tmp_path / "backend/security.py").write_text("""
password = "super_secret_admin_password_123"
eval("print('unsafe')")
""")

    res = checker.validate(tmp_path)
    assert any("Hardcoded Secret" in err for err in res.errors)
    assert any("Unsafe Execution API" in err for err in res.errors)


def test_performance_checker(tmp_path):
    checker = PerformanceChecker()

    (tmp_path / "backend").mkdir()
    (tmp_path / "backend/app.py").write_text("\n" * 400) # Oversized LOC file (>300 lines)

    res = checker.validate(tmp_path)
    assert any("Oversized file" in warn for warn in res.warnings)
    assert res.metadata["total_loc"] >= 400


def test_quality_score_calculation():
    calculator = QualityScoreCalculator()

    results = [
        ValidationResult(validator="Syntax Checker", status="PASS", score=95.0, execution_time=0.1),
        ValidationResult(validator="Security Checker", status="PASS", score=100.0, execution_time=0.1),
        ValidationResult(validator="Performance Checker", status="PASS", score=90.0, execution_time=0.1)
    ]

    quality = calculator.compute_score(results)
    assert quality.overall_score >= 90.0
    assert quality.grade in {"A+", "A", "B+", "B"}
    assert quality.ready_for_export is True


@pytest.mark.anyio
@patch("backend.validation.validator.ValidationOrchestrator.run_all_checks")
async def test_validator_orchestration_loop(mock_run, tmp_path):
    orchestrator = ValidationOrchestrator()

    mock_run.return_value = [
        ValidationResult(validator="Syntax Checker", status="PASS", score=95.0, errors=[], warnings=[], execution_time=0.1),
        ValidationResult(validator="Security Checker", status="PASS", score=100.0, errors=[], warnings=[], execution_time=0.1),
        ValidationResult(validator="Performance Checker", status="PASS", score=92.0, errors=[], warnings=[], execution_time=0.1),
    ]

    # Run orchestration
    report, ready = await orchestrator.execute_validation_pipeline(
        project_name="HMS-System",
        project_path=tmp_path
    )

    assert ready is True
    assert report.quality.overall_score >= 90.0
    assert (tmp_path / "reports/validation_report.json").exists()
    assert (tmp_path / "reports/quality_report.json").exists()
    assert (tmp_path / "reports/metrics.json").exists()
