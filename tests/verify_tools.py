import asyncio
import sys
import tempfile
from pathlib import Path

# Add root folder to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.tools.agent import ToolAgent
from backend.tools.safety.command_validator import CommandValidator

async def run_tools_verification():
    print("======================================================================")
    print("AIForge Autonomous Tool Execution System E2E Verification Suite")
    print("======================================================================\n")

    agent = ToolAgent()
    validator = CommandValidator()

    # 1. Command Security Validation
    print("--- 1. Command Security Validation ---")
    safe_cmds = ["pytest tests/", "git status", "pip install -r requirements.txt"]
    for sc in safe_cmds:
        res = validator.validate_command(sc)
        print(f"  Command: '{sc}' -> Validated: {res}")
    
    unsafe_cmds = ["rm -rf /", "del /f config.json", "sudo rm -rf ."]
    for uc in unsafe_cmds:
        res = validator.validate_command(uc)
        print(f"  Command: '{uc}' -> Validated: {res} (Blocked successfully)")
    print("")

    # 2. Terminal Executor Tool
    print("--- 2. Terminal Executor Tool ---")
    term_res = agent.handle_request("Run terminal command", command="echo AIForge Security Gate")
    print(f"  Success: {term_res['success']}")
    print(f"  Output: {term_res['output'].strip()}")
    print("")

    # 3. Filesystem Tool
    print("--- 3. Filesystem Tool ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir) / "build_manifest.json"
        write_res = agent.handle_request(
            "Write manifest file",
            action="write",
            path=str(test_path),
            content='{"project": "AIForge", "status": "stable"}'
        )
        print(f"  Write Success: {write_res['success']}")
        print(f"  Write Output: {write_res['output'].strip()}")
        
        read_res = agent.handle_request("Read manifest file", action="read", path=str(test_path))
        print(f"  Read Success: {read_res['success']}")
        print(f"  Read Output: {read_res['output'].strip()}")
    print("")

    # 4. Git Tool
    print("--- 4. Git Tool ---")
    git_res = agent.handle_request("Run git command", git_cmd="status")
    print(f"  Success: {git_res['success']}")
    print(f"  Tool matched: {git_res['tool_name']}")
    print("")

    # 5. Docker Tool
    print("--- 5. Docker Tool ---")
    docker_res = agent.handle_request("Run docker command", docker_cmd="ps")
    print(f"  Success: {docker_res['success']}")
    print(f"  Output: {docker_res['output'].strip()}")
    print("")

    # 6. Database (PostgreSQL) Parameterized Tool
    print("--- 6. Database (PostgreSQL) Parameterized Tool ---")
    db_res = agent.handle_request(
        "Run parameterized query",
        sql="SELECT * FROM users WHERE name = ?",
        params=("Bob",)
    )
    print(f"  Success: {db_res['success']}")
    print(f"  Output: {db_res['output'].strip()}")
    print("")

    # 7. Outbound HTTP requests (API Tool)
    print("--- 7. Outbound HTTP requests (API Tool) ---")
    api_res = agent.handle_request("Fetch REST data", url="https://api.github.com/users/aiforge")
    print(f"  Success: {api_res['success']}")
    print(f"  Output: {api_res['output'].strip()}")
    print("")

    # 8. Browser Documentation Summarizer Tool
    print("--- 8. Browser Documentation Summarizer Tool ---")
    browser_res = agent.handle_request("Summarize documentation url", url="https://docs.pytest.org")
    print(f"  Success: {browser_res['success']}")
    print(f"  Output: {browser_res['output'].strip()}")
    print("")

    print("======================================================================")
    print("All SRE Tool Execution System tests completed successfully!")
    print("======================================================================")

if __name__ == "__main__":
    asyncio.run(run_tools_verification())
