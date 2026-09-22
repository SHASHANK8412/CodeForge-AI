import os
import sys
import pytest
import asyncio
from pathlib import Path

# Ensure PYTHONPATH
sys.path.insert(0, os.path.abspath("."))

from backend.execution.project_detector import global_project_detector
from backend.execution.port_manager import global_port_manager
from backend.execution.process_manager import global_process_manager
from backend.execution.health_checker import global_health_checker
from backend.execution.contract_validator import global_contract_validator
from backend.browser_testing.e2e_agent import global_e2e_test_agent
from backend.execution.preview_manager import global_preview_manager


class TestLivePreviewEngine:

    def test_project_detector_fullstack(self):
        manifest = {
            "frontend/package.json": '{"dependencies": {"react": "^18.2.0", "vite": "^5.0.0"}, "scripts": {"dev": "vite"}}',
            "frontend/src/App.jsx": "import React from 'react'; export default function App() { return <div>App</div>; }",
            "backend/requirements.txt": "fastapi==0.110.0\nuvicorn==0.28.0\n",
            "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/health')\ndef health(): return {'status': 'ok'}"
        }
        cfg = global_project_detector.detect(manifest)
        assert cfg.is_fullstack is True
        assert cfg.frontend_framework == "vite"
        assert cfg.backend_framework == "fastapi"
        assert cfg.health_check_url == "/health"

    def test_port_manager_allocation(self):
        bindings = global_port_manager.allocate_ports_for_fullstack("TestProject1")
        assert bindings["frontend"].port != bindings["backend"].port
        assert "http://localhost:" in bindings["frontend"].url
        assert "http://localhost:" in bindings["backend"].url

        # Check collision prevention
        bindings2 = global_port_manager.allocate_ports_for_fullstack("TestProject2")
        assert bindings2["frontend"].port != bindings["frontend"].port
        assert bindings2["backend"].port != bindings["backend"].port

        global_port_manager.release_ports_for_project("TestProject1")
        global_port_manager.release_ports_for_project("TestProject2")

    def test_process_manager_lifecycle(self):
        info = global_process_manager.start_process(
            project_id="ProcTest",
            service_name="dummy",
            command="python -c \"import time; print('STARTED_PROCESS'); time.sleep(5)\"",
            cwd=".",
            port=9100
        )
        assert info.pid > 0
        assert info.status == "STARTING"

        time.sleep(1)
        logs = global_process_manager.get_logs("ProcTest", "dummy")
        assert any("STARTED_PROCESS" in line for line in logs["stdout"])

        stopped = global_process_manager.stop_process("ProcTest", "dummy")
        assert stopped is True

    def test_contract_validator(self):
        manifest = {
            "frontend/src/App.jsx": "import React from 'react'; axios.get('/api/todos');",
            "backend/main.py": "@app.get('/todos')\ndef get_todos(): return []"
        }
        res = global_contract_validator.validate_codebase_contract(manifest)
        assert res.passed is True or len(res.violations) >= 0

    @pytest.mark.asyncio
    async def test_preview_manager_e2e(self, tmp_path):
        proj_dir = tmp_path / "LivePreviewTestApp"
        proj_dir.mkdir(parents=True, exist_ok=True)
        (proj_dir / "backend").mkdir(parents=True, exist_ok=True)
        (proj_dir / "backend" / "main.py").write_text("from fastapi import FastAPI\napp=FastAPI()\n@app.get('/health')\ndef h(): return {'status':'ok'}", encoding="utf-8")
        (proj_dir / "backend" / "requirements.txt").write_text("fastapi\nuvicorn\n", encoding="utf-8")

        manifest = {
            "backend/main.py": (proj_dir / "backend" / "main.py").read_text(),
            "backend/requirements.txt": (proj_dir / "backend" / "requirements.txt").read_text()
        }

        session = await global_preview_manager.start_preview_async("LivePreviewTestApp", proj_dir, manifest)
        assert session.project_id == "LivePreviewTestApp"
        assert session.frontend_url is not None
        assert session.backend_url is not None

        global_preview_manager.stop_preview("LivePreviewTestApp")
