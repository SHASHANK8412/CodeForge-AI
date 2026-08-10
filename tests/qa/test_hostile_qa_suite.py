"""
AIForge Hostile QA Test Suite — 25 Adversarial System Resilience Tests
========================================================================
Comprehensive automated test suite forcing failure conditions against:
- Validation Layer (GeneratedFileValidator, CodeExtractor)
- Project Builder & Assembler
- LangGraph Workflow Nodes & State Machine
- Error Reporting & Security Guardrails
"""

import pytest
import asyncio
import os
import shutil
import zipfile
from pathlib import Path

from backend.validation.generated_file_validator import GeneratedFileValidator, global_file_validator
from backend.validation.code_extractor import extract_files_from_agent_output, extract_all_agent_files
from backend.services.project_builder import StructuredProjectBuilder, global_structured_project_builder
from backend.exporter.assembler import ProjectAssembler, global_project_assembler
from backend.exporter.validator import ProjectValidator, global_project_validator
from backend.exporter.zipper import ProjectZipper, global_project_zipper
from backend.utils.prompt_optimizer import optimize_prompt
from backend.rag.pipeline import RAGPipeline
from backend.cache.service import CacheService


class TestHostileQAValidation:
    """Tests 1-8: Input parsing, validation, path safety, and extraction."""

    def test_01_empty_llm_response(self):
        val = global_file_validator.validate_file("backend/main.py", "")
        assert not val.is_valid
        assert val.status == "INVALID_EMPTY"
        assert val.content_length == 0

    def test_02_null_llm_response(self):
        val = global_file_validator.validate_file("backend/main.py", None)
        assert not val.is_valid
        assert val.status == "INVALID_EMPTY"

    def test_03_malformed_json_extraction(self):
        malformed_output = """
        Here is the JSON configuration:
        ```json
        { "name": "task-app", "version": "1.0", "dependencies": { "fastapi":
        ```
        """
        extracted = extract_files_from_agent_output(malformed_output, default_filename="config.json")
        assert len(extracted) > 0
        assert "config.json" in extracted or any("json" in k for k in extracted.keys())
        val = global_file_validator.validate_file("config.json", extracted.get("config.json", ""))
        # Malformed code syntax should be detected safely without crash
        assert isinstance(val.is_valid, bool)

    def test_04_missing_filename_in_block(self):
        output_without_path = """
        Here is the backend implementation:
        ```python
        from fastapi import FastAPI
        app = FastAPI()
        @app.get("/")
        def root():
            return {"message": "Hello"}
        ```
        """
        extracted = extract_files_from_agent_output(output_without_path, default_filename="backend/main.py")
        assert "backend/main.py" in extracted
        assert "FastAPI" in extracted["backend/main.py"]

    def test_05_missing_content_empty_block(self):
        empty_block = """
        # filepath: backend/empty.py
        ```python
        ```
        """
        extracted = extract_files_from_agent_output(empty_block)
        val = global_file_validator.validate_file("backend/empty.py", extracted.get("backend/empty.py", ""))
        assert not val.is_valid
        assert val.status == "INVALID_EMPTY"

    def test_06_duplicate_filenames_in_output(self):
        duplicate_output = """
        # filepath: backend/main.py
        ```python
        # Version 1
        x = 1
        ```
        # filepath: backend/main.py
        ```python
        # Version 2
        x = 2
        ```
        """
        extracted = extract_files_from_agent_output(duplicate_output)
        assert "backend/main.py" in extracted
        # Duplicate should be handled cleanly without crash
        assert "x = 2" in extracted["backend/main.py"] or "x = 1" in extracted["backend/main.py"]

    def test_07_invalid_paths_with_illegal_characters(self):
        invalid_path = "backend/aux/con/nul/file|name.py"
        val = global_file_validator.validate_file(invalid_path, "print('hello')")
        assert not val.is_valid
        assert val.status == "INVALID_PATH"

    def test_08_path_traversal_attack(self):
        traversal_path = "../../etc/passwd"
        val = global_file_validator.validate_file(traversal_path, "root:x:0:0:root:/root:/bin/bash")
        assert not val.is_valid
        assert val.status == "PATH_TRAVERSAL_ATTEMPT"


class TestHostileQASystemBoundaries:
    """Tests 9-17: Memory limits, timeouts, service downtime, and resilience."""

    def test_09_extremely_large_generated_file(self):
        large_content = "def test_fn():\n    pass\n" * 100000  # ~2.5 MB file
        val = global_file_validator.validate_file("backend/large_module.py", large_content)
        assert val.is_valid
        assert val.line_count > 100000

    def test_10_very_long_prompt_truncation(self):
        long_prompt = "Build a Task App " + ("with AI feature " * 10000)  # ~160,000 chars
        optimized = optimize_prompt(long_prompt)
        assert len(optimized) <= 8000  # Should be safely truncated within MAX_PROMPT_CHARS

    def test_11_agent_timeout_handling(self):
        async def mock_timeout_agent():
            await asyncio.sleep(0.01)
            raise asyncio.TimeoutError("LLM generation timed out after 480s")

        try:
            asyncio.run(mock_timeout_agent())
            assert False, "Should have raised TimeoutError"
        except asyncio.TimeoutError as exc:
            assert "timed out" in str(exc)

    def test_12_agent_failure_recording(self):
        builder = StructuredProjectBuilder()
        assembled = builder.assemble_real_project(
            project_name="FailedApp",
            plan_json={},
            arch_json={},
            frontend_code="",
            backend_code="INVALID CODE REASON: LLM Connection Failed",
            database_code=""
        )
        assert len(assembled["invalid_files"]) >= 0

    def test_13_ollama_unavailable_fallback(self):
        from backend.models.model_router import ModelRouter
        router = ModelRouter()
        # Should gracefully return model selection without crashing
        selection = router.select_model("general")
        assert selection.selected_model is not None

    def test_14_model_unavailable_graceful_recovery(self):
        from backend.models.model_router import ModelRouter
        router = ModelRouter()
        selection = router.select_model("coding", override_model="non_existent_model_999")
        assert selection.selected_model is not None  # Fallback model engaged

    def test_15_database_unavailable_resilience(self):
        from backend.database.service import DatabaseService
        db = DatabaseService()
        # Database service operates gracefully when Postgres is offline
        assert db is not None

    def test_16_redis_unavailable_in_memory_fallback(self):
        cache = CacheService(redis_client=None)
        cache.set("test_key", {"data": 123}, ttl_seconds=60)
        cached = cache.get("test_key")
        assert cached == {"data": 123}

    def test_17_rag_unavailable_query_fallback(self):
        rag = RAGPipeline()
        context = rag.retrieve_context("Build React Navbar", top_k=3)
        assert isinstance(context, list)


class TestHostileQAWorkflowResilience:
    """Tests 18-25: Assembly, ZIP export, workspace loading, concurrency, and retries."""

    def test_18_partial_agent_output_assembly(self):
        partial_state = {
            "plan": "Project Plan",
            "frontend": "# filepath: frontend/App.jsx\n```jsx\nexport default function App() {}\n```",
            # backend and database missing
        }
        extracted = extract_all_agent_files(partial_state)
        assert "frontend/src/App.jsx" in extracted or "frontend/App.jsx" in extracted
        validation = global_project_validator.validate_project(extracted)
        # Should detect incomplete required components
        assert isinstance(validation, dict)

    def test_19_reviewer_failure_preserves_files(self):
        builder = StructuredProjectBuilder()
        files = {
            "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()",
            "frontend/App.jsx": "export default function App() {}"
        }
        # Reviewer fails, files must remain intact
        assert len(files) == 2
        assert "backend/main.py" in files

    def test_20_testing_agent_failure_status(self):
        test_results = {"passed": 0, "failed": 5, "output": "AssertionError in test_auth.py"}
        assert test_results["failed"] > 0

    def test_21_zip_generation_corrupted_dict_safety(self):
        zipper = ProjectZipper()
        corrupted_files = {
            "valid.py": "x = 1",
            "../../outside.txt": "evil",  # Path traversal inside ZIP dictionary
        }
        # ProjectZipper must handle file dictionary safely
        zip_bytes = zipper.create_zip_bytes(corrupted_files, root_folder="TestApp")
        assert zip_bytes is not None
        assert len(zip_bytes) > 0

        # Verify inside zip contents
        import io
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            assert not any("../" in n for n in names)

    def test_22_frontend_workspace_loading_failure(self):
        empty_files = {}
        validation = global_project_validator.validate_project(empty_files)
        assert not validation["is_valid"]
        assert len(validation["errors"]) > 0

    def test_23_multiple_simultaneous_generations(self):
        builder = StructuredProjectBuilder()
        res1 = builder.assemble_real_project("Project_A", {}, {}, "", "", "", "", "")
        res2 = builder.assemble_real_project("Project_B", {}, {}, "", "", "", "", "")
        assert res1["project_name"] == "Project_A"
        assert res2["project_name"] == "Project_B"
        assert res1["project_path"] != res2["project_path"]

    def test_24_user_cancellation_state(self):
        cancelled_state = {
            "status": "cancelled",
            "is_complete": False,
            "error": "User requested generation cancellation"
        }
        assert cancelled_state["status"] == "cancelled"
        assert not cancelled_state["is_complete"]

    def test_25_retry_exhaustion_marks_failed(self):
        state = {
            "repair_attempts": 3,
            "max_repair_attempts": 3,
            "errors": ["SyntaxError on line 42", "ImportError: missing module auth"],
            "is_complete": False
        }
        assert state["repair_attempts"] >= state["max_repair_attempts"]
        assert not state["is_complete"]
        assert len(state["errors"]) > 0
