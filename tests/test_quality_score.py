import pytest
from backend.review.quality_score import QualityScoreCalculator


def test_quality_score_subscores():
    calculator = QualityScoreCalculator()

    # Pass mock findings designed to trigger these specific scores
    findings = [
        {"severity": "info", "issue": "naming inconsistency"}, # Deducts slightly from maintainability
        {"severity": "warning", "issue": "circular import dependency"}, # Deducts slightly from architecture
        {"severity": "info", "issue": "missing module docstring"}, # Deducts slightly from documentation
    ]

    test_results = {
        "passed": 10,
        "failed": 0,
        "errors": 0
    }

    scores = calculator.calculate_scores(findings, test_results)

    # Validate overall and subscores calculation structure
    assert "overall" in scores
    assert "architecture" in scores
    assert "security" in scores
    assert "performance" in scores
    assert "maintainability" in scores
    assert "testing" in scores

    assert scores["testing"] == 10.0
    assert scores["overall"] >= 8.0
    assert scores["security"] == 10.0 # No security issues
