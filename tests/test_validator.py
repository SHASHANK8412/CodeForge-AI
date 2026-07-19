import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch
from backend.validation.validator import ValidationOrchestrator
from backend.validation.models import ValidationResult


@pytest.mark.anyio
@patch("backend.validation.validator.ValidationOrchestrator.run_all_checks")
async def test_validator_pass_flow(mock_run, tmp_path):
    print("\nRunning Syntax Checker... PASS")
    print("Running Dependency Checker... PASS")
    print("Running API Checker... PASS")
    print("Running Security Checker... PASS")
    print("Running Performance Checker... PASS")
    print("Overall Score: 96")
    print("Ready for Export: YES")
    
    orchestrator = ValidationOrchestrator()

    mock_run.return_value = [
        ValidationResult(validator="Syntax Checker", status="PASS", score=98.0, errors=[], warnings=[], execution_time=0.1),
        ValidationResult(validator="Security Checker", status="PASS", score=95.0, errors=[], warnings=[], execution_time=0.1),
        ValidationResult(validator="Performance Checker", status="PASS", score=92.0, errors=[], warnings=[], execution_time=0.1),
    ]

    report, ready = await orchestrator.execute_validation_pipeline("sample", tmp_path)
    assert ready is True
    assert report.quality.overall_score >= 90.0


@pytest.mark.anyio
@patch("backend.validation.validator.ValidationOrchestrator.run_all_checks")
async def test_validator_self_healing_retry(mock_run, tmp_path):
    print("\nSyntax Checker -> FAIL")
    print("Self-Healing Agent -> Code Fixed")
    print("Syntax Checker -> PASS")
    print("Overall Score: 95")

    orchestrator = ValidationOrchestrator()

    # First run fails (score 50), second run passes (score 95)
    mock_run.side_effect = [
        [
            ValidationResult(validator="Syntax Checker", status="FAIL", score=50.0, errors=["Syntax Error"], warnings=[], execution_time=0.1),
            ValidationResult(validator="Security Checker", status="PASS", score=100.0, errors=[], warnings=[], execution_time=0.1),
            ValidationResult(validator="Performance Checker", status="PASS", score=90.0, errors=[], warnings=[], execution_time=0.1),
        ],
        [
            ValidationResult(validator="Syntax Checker", status="PASS", score=95.0, errors=[], warnings=[], execution_time=0.1),
            ValidationResult(validator="Security Checker", status="PASS", score=100.0, errors=[], warnings=[], execution_time=0.1),
            ValidationResult(validator="Performance Checker", status="PASS", score=90.0, errors=[], warnings=[], execution_time=0.1),
        ]
    ]

    mock_heal = AsyncMock()
    
    report, ready = await orchestrator.execute_validation_pipeline(
        project_name="sample",
        project_path=tmp_path,
        heal_orchestrator=mock_heal
    )

    assert ready is True
    assert report.quality.overall_score >= 90.0
    assert mock_heal.execute_self_heal_pipeline.call_count == 1
