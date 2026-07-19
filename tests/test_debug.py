import json
import pytest
from unittest.mock import patch
from backend.review.debug import DebugAgent


@pytest.mark.anyio
@patch("backend.review.debug.generate_text_async")
async def test_debug_agent_identifies_root_cause(mock_gen):
    agent = DebugAgent()

    # Mock response matching specifications
    mock_gen.return_value = json.dumps({
        "root_cause": "JWT authentication failed",
        "explanation": "Token validation issue",
        "proposed_fix": "Update JWT validation middleware",
        "confidence_score": 0.95
    })

    traceback_log = """
    AssertionError
    Expected 200
    Received 401
    """

    result = await agent.debug_failures(traceback_log, "pytest log", ["backend/main.py"])

    assert result["confidence_score"] == 0.95
    assert "JWT" in result["root_cause"]
    assert "middleware" in result["proposed_fix"]
