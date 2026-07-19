import pytest
from backend.validation.models import ValidationResult
from backend.validation.quality_score import QualityScoreCalculator


def test_quality_score_weighted_output():
    calculator = QualityScoreCalculator()

    results = [
        ValidationResult(validator="Syntax Checker", status="PASS", score=98.0, errors=[], warnings=[], execution_time=0.1),
        ValidationResult(validator="Security Checker", status="PASS", score=95.0, errors=[], warnings=[], execution_time=0.1),
        ValidationResult(validator="Performance Checker", status="PASS", score=92.0, errors=[], warnings=[], execution_time=0.1)
    ]

    quality = calculator.compute_score(results)
    
    assert quality.overall_score >= 90.0
    assert quality.grade in {"A+", "A", "B+"}
    assert quality.ready_for_export is True
