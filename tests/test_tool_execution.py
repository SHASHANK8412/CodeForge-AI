import pytest
import tempfile
from pathlib import Path

from backend.tools.agent import ToolAgent
from backend.tools.safety.command_validator import CommandValidator

def test_command_validator():
    validator = CommandValidator()
    
    # Safe commands
    assert validator.validate_command("pytest tests/") is True
    assert validator.validate_command("git status") is True
    assert validator.validate_command("npm install") is True

    # Dangerous commands
    assert validator.validate_command("rm -rf /") is False
    assert validator.validate_command("sudo rm file") is False
    assert validator.validate_command("del /f config.json") is False

def test_tool_agent_routing():
    agent = ToolAgent()
    
    # Git routing
    git_res = agent.handle_request("Run git status", git_cmd="status")
    assert git_res["tool_name"] == "GitTool"

    # Terminal routing
    term_res = agent.handle_request("Run pytest tests/", command="echo hello")
    assert term_res["tool_name"] == "TerminalTool"
    assert term_res["success"] is True

def test_filesystem_tool():
    agent = ToolAgent()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        
        # Write
        write_res = agent.handle_request(
            "Write file",
            action="write",
            path=str(test_file),
            content="AIForge Tool System"
        )
        assert write_res["success"] is True
        
        # Read
        read_res = agent.handle_request(
            "Read file",
            action="read",
            path=str(test_file)
        )
        assert read_res["success"] is True
        assert read_res["output"] == "AIForge Tool System"

def test_postgres_tool():
    agent = ToolAgent()
    
    # Select from users
    db_res = agent.handle_request(
        "Run sql query",
        sql="SELECT * FROM users WHERE name = ?",
        params=("Alice",)
    )
    assert db_res["success"] is True
    assert "[]" in db_res["output"]

def test_api_and_browser_tools():
    agent = ToolAgent()
    
    # API requests
    api_res = agent.handle_request("Fetch API data", url="https://api.github.com/repos/aiforge")
    assert api_res["success"] is True
    assert "url_accessed" in api_res["output"]

    # Browser parsing
    browser_res = agent.handle_request("Browse documentation url", url="https://fastapi.tiangolo.com")
    assert browser_res["success"] is True
    assert "FastAPI" in browser_res["output"]
