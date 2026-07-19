import json
import pytest
from pathlib import Path
from unittest.mock import patch
from backend.review.reviewer import Reviewer


@pytest.mark.anyio
@patch("backend.review.reviewer.generate_text_async")
async def test_reviewer_finds_issues(mock_gen, tmp_path):
    reviewer = Reviewer()

    # Mock response matching input prompt expectations
    mock_gen.return_value = json.dumps([
        {
            "severity": "critical",
            "file": "app.py",
            "line": 1,
            "issue": "Hardcoded password, security vulnerability",
            "recommendation": "Use environment variables"
        }
    ])

    test_file = tmp_path / "app.py"
    test_file.write_text("""password = "admin123"

def login():
    print(password)
""")

    findings = await reviewer.review_file(tmp_path, "app.py")

    assert len(findings) == 1
    issue = findings[0]
    assert issue["severity"] == "critical"
    assert "Hardcoded password" in issue["issue"]
    assert "environment variables" in issue["recommendation"]
