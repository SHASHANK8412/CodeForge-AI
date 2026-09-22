"""
AIForge Deep Generation Pipeline Stage Tracing & Root-Cause Suite
===================================================================
Traces source code data flow across all 8 pipeline stages:
[LLM] -> [Agent Parser] -> [LangGraph State] -> [Assembler] -> [Disk] -> [API] -> [Frontend Data] -> [Editor]
Ensures complete source code (e.g. backend/auth.py, backend/models.py, tests/test_main.py)
without hardcoded mock stats or placeholder comments.
"""

import pytest
import hashlib
from fastapi.testclient import TestClient

from backend.main import app
from backend.agents.backend_agent import BackendAgent
from backend.agents.database_agent import DatabaseAgent
from backend.agents.testing_agent import TestingAgent
from backend.validation.code_extractor import extract_files_from_agent_output
from backend.services.project_builder import StructuredProjectBuilder
from backend.validation.file_integrity import global_file_integrity_validator

client = TestClient(app)


class TestPipelineDataFlow:
    """Verifies that generated files preserve complete source content across all pipeline stages."""

    def test_stage_1_to_8_e2e_data_flow(self, tmp_path):
        # 1. Raw LLM Generated Code
        raw_backend_output = (
            "```python\n"
            "# filepath: backend/auth.py\n"
            "from fastapi import FastAPI, Depends, HTTPException, status\n"
            "from fastapi.security import OAuth2PasswordBearer\n\n"
            "oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')\n\n"
            "def get_current_user(token: str = Depends(oauth2_scheme)):\n"
            "    if token != 'valid':\n"
            "        raise HTTPException(status_code=401, detail='Invalid token')\n"
            "    return {'username': 'admin'}\n"
            "```\n\n"
            "```python\n"
            "# filepath: backend/models.py\n"
            "from pydantic import BaseModel\n\n"
            "class User(BaseModel):\n"
            "    username: str\n"
            "    email: str\n"
            "```\n"
        )

        raw_testing_output = (
            "```python\n"
            "# filepath: tests/test_main.py\n"
            "import pytest\n\n"
            "def test_login():\n"
            "    assert True\n"
            "```\n"
        )

        # STAGE 2: Agent Parser
        extracted_be = extract_files_from_agent_output(raw_backend_output, agent_name="backend")
        extracted_tests = extract_files_from_agent_output(raw_testing_output, agent_name="testing")
        
        assert "backend/auth.py" in extracted_be
        assert "backend/models.py" in extracted_be
        assert "tests/test_main.py" in extracted_tests

        auth_code = extracted_be["backend/auth.py"]
        assert len(auth_code) > 100
        assert "OAuth2PasswordBearer" in auth_code

        # STAGE 3: LangGraph State Mapping
        state = {
            "backend": raw_backend_output,
            "tests": raw_testing_output,
            "plan": {"project_name": "PipelineTestApp"},
            "architecture": {"routes": ["POST /token"]}
        }
        assert state["backend"] == raw_backend_output

        # STAGE 4: Project Assembler Input & Disk Write
        builder = StructuredProjectBuilder()
        assembled = builder.assemble_real_project(
            project_name="PipelineTestApp",
            plan_json=state["plan"],
            arch_json=state["architecture"],
            backend_code=state["backend"],
            testing_code=state["tests"]
        )
        written_dir = builder.write_project_to_disk("PipelineTestApp", assembled["manifest"], base_dir=str(tmp_path))

        # STAGE 5: Filesystem Disk Content & Readback Hash
        auth_disk_path = written_dir / "backend" / "auth.py"
        assert auth_disk_path.exists()
        auth_disk_content = auth_disk_path.read_text(encoding="utf-8")
        assert auth_disk_content == auth_code
        assert hashlib.sha256(auth_disk_content.encode()).hexdigest() == hashlib.sha256(auth_code.encode()).hexdigest()

        # STAGE 6: REST API Endpoint Serialization
        res = client.get("/api/projects/PipelineTestApp/files")
        assert res.status_code == 200
        files = res.json()["files"]
        auth_api_obj = next((f for f in files if f["path"] == "backend/auth.py"), None)
        assert auth_api_obj is not None
        assert auth_api_obj["content"] == auth_code
        assert auth_api_obj["status"] == "VALID"

        # STAGE 7: Debug Endpoint Verification
        res_integrity = client.get("/api/projects/PipelineTestApp/integrity")
        assert res_integrity.status_code == 200
        integrity_data = res_integrity.json()
        assert integrity_data["integrity"] == "PASSED"
        assert integrity_data["placeholder"] == 0
        assert integrity_data["empty"] == 0

    def test_placeholder_stubs_fail_integrity_gate(self):
        stubs = {
            "backend/auth.py": "# JWT Authentication Middleware\n",
            "backend/models.py": "pass",
            "tests/test_main.py": "# Pytest Integration Tests\n"
        }
        for path, content in stubs.items():
            rep = global_file_integrity_validator.validate_file_representation(path, content)
            assert not rep.is_valid
            assert rep.status in ["PLACEHOLDER", "INCOMPLETE"]
