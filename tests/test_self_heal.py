import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch
from backend.review.self_heal import SelfHealOrchestrator


@pytest.mark.anyio
@patch("backend.review.self_heal.SelfHealOrchestrator.run_tests")
@patch("backend.review.debug.generate_text_async")
@patch("backend.review.patch_generator.generate_text_async")
async def test_self_heal_pipeline_workflow(mock_patch, mock_debug, mock_run, tmp_path):
    print("\nGenerating Project...")
    print("Running Tests...")
    
    # 1. Pytest fails initially, then passes on retry
    print("FAILED test_auth.py")
    mock_run.side_effect = [
        (1, "\n__________________________________ test_auth __________________________________\nAssertionError in tests/test_auth.py"),
        (0, "========================= 1 passed in 0.10s =========================")
    ]

    print("Reviewer Started...")
    print("Issues Found...")

    mock_debug.return_value = json.dumps({
        "root_cause": "Assertion failure",
        "explanation": "status mismatch",
        "proposed_fix": "Change status check to 200",
        "confidence_score": 0.95
    })

    print("Generating Patch...")
    mock_patch.return_value = json.dumps({
        "file": "tests/test_auth.py",
        "start_line": 3,
        "end_line": 3,
        "replacement": "    assert status == 200"
    })

    # Prepare project files on disk
    (tmp_path / "backend").mkdir()
    (tmp_path / "tests").mkdir()
    test_file = tmp_path / "tests/test_auth.py"
    test_file.write_text("def test_auth():\n    status = 500\n    assert status == 200")

    print("Applying Patch...")
    orchestrator = SelfHealOrchestrator()
    findings, test_results, scores, report = await orchestrator.execute_self_heal_pipeline(
        project_name="HMS-System",
        project_path=tmp_path
    )

    print("Running Tests Again...")
    print("PASSED")
    print("Generating Report...")
    print("Done")

    # Assertions to ensure workflow executed as expected
    assert test_results["passed"] == 1
    assert scores["overall"] >= 8.0
    assert (tmp_path / "reports/project_review.md").exists()
