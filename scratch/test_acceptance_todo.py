import asyncio
import os
import sys
import hashlib
from pathlib import Path

# Set PYTHONPATH
sys.path.insert(0, os.path.abspath("."))

from backend.graph.parallel_workflow import parallel_graph
from backend.validation.file_integrity import global_file_integrity_validator
from backend.validation.generated_file_validator import global_file_validator

async def run_acceptance():
    prompt = "Build a production-ready full-stack Todo application using React, FastAPI and PostgreSQL with JWT authentication."
    print(f"Running E2E Acceptance Test for: '{prompt}'")

    res = await parallel_graph.ainvoke({"user_prompt": prompt})
    
    files = res.get("files", {})
    print(f"\nTotal Generated Files: {len(files)}")
    
    required_paths = [
        "backend/main.py",
        "backend/auth.py",
        "backend/models.py",
        "database/schema.sql",
        "frontend/src/App.jsx"
    ]
    
    for req in required_paths:
        assert req in files, f"Missing required file: {req}"
        content = files[req]

    test_file_found = any(k.startswith("tests/") and k.endswith(".py") for k in files)
    assert test_file_found, "Missing test suite file in tests/"
        
        # 1. Non-placeholder check
        assert content.strip() != "# JWT Authentication Middleware", f"{req} contains placeholder title comment"
        assert content.strip() != "# Pytest Integration Tests", f"{req} contains placeholder title comment"
        assert content.strip() != "pass", f"{req} contains pass stub"
        
        # 2. File integrity validation
        rep = global_file_integrity_validator.validate_file_representation(req, content)
        assert rep.is_valid, f"{req} failed integrity validation: {rep.error_message}"
        
        # 3. File validator check
        val = global_file_validator.validate_file(req, content)
        assert val.is_valid, f"{req} failed file validator: {val.errors}"
        
        print(f"  [OK] {req} ({rep.lines} lines, {rep.size} bytes, status={rep.status})")

    project_path = Path(res.get("project_path", ""))
    print(f"\nFilesystem Directory: {project_path}")
    assert project_path.exists(), f"Project directory does not exist on disk: {project_path}"

    for req in required_paths:
        disk_file = project_path / req
        assert disk_file.exists(), f"File missing on disk: {disk_file}"
        disk_text = disk_file.read_text(encoding="utf-8")
        assert disk_text == files[req], f"Disk content mismatch for {req}"
        assert hashlib.sha256(disk_text.encode()).hexdigest() == hashlib.sha256(files[req].encode()).hexdigest()

    print("\nACCEPTANCE TEST PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(run_acceptance())
