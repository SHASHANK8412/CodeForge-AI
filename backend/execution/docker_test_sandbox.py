"""
Run a generated project's Python tests inside a throwaway Docker container.

The container sees only the project folder (mounted at /app), installs the project's own
requirements with a shared pip cache, and runs pytest with an empty config. Nothing is installed
on the host, and the generated code never runs in AIForge's process or environment.

Mode (AIFORGE_TEST_SANDBOX): "auto" (default) uses Docker when its daemon is reachable and falls
back to the local per-project venv; "docker" requires Docker; "local" never uses it.
"""

import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Optional

from backend.execution.models import ExecutionResult, ExecutionStatus, ExecutionType
from backend.execution.project_env import requirements_file

IMAGE = os.environ.get("AIFORGE_TEST_IMAGE", "python:3.13-slim")
PIP_CACHE_VOLUME = "aiforge-pip-cache"


def sandbox_mode() -> str:
    mode = os.environ.get("AIFORGE_TEST_SANDBOX", "auto").strip().lower()
    return mode if mode in ("auto", "docker", "local") else "auto"


_docker_ok: Optional[bool] = None


def docker_exe() -> Optional[str]:
    """The docker CLI: on PATH, or in Docker Desktop's default install folders on Windows."""
    found = shutil.which("docker")
    if found:
        return found
    for base in (os.environ.get("LOCALAPPDATA", ""), os.environ.get("ProgramFiles", "")):
        for sub in ("Programs/DockerDesktop/resources/bin/docker.exe", "Docker/Docker/resources/bin/docker.exe"):
            candidate = Path(base) / sub
            if base and candidate.is_file():
                return str(candidate)
    return None


def docker_available() -> bool:
    """Whether a Docker daemon answers (cached for the process; it is checked once)."""
    global _docker_ok
    if _docker_ok is None:
        exe = docker_exe()
        try:
            _docker_ok = bool(exe) and subprocess.run([exe, "info"], capture_output=True, timeout=10).returncode == 0
        except (OSError, subprocess.SubprocessError):
            _docker_ok = False
    return _docker_ok


def should_use_docker() -> bool:
    mode = sandbox_mode()
    return mode == "docker" or (mode == "auto" and docker_available())


def run_pytest_in_docker(project_path: Path, timeout_seconds: float = 900.0) -> ExecutionResult:
    project_path = Path(project_path).resolve()
    req = requirements_file(project_path)
    req_rel = req.relative_to(project_path).as_posix() if req else None
    install = (f"pip install -q --disable-pip-version-check --root-user-action=ignore -r {req_rel} pytest"
               if req_rel else "pip install -q --disable-pip-version-check --root-user-action=ignore pytest")
    script = (
        f"{install} > /tmp/pip.log 2>&1 || {{ echo 'Dependency install failed:'; tail -40 /tmp/pip.log; exit 3; }}; "
        "printf '[pytest]\\n' > /tmp/aiforge_pytest.ini; "
        "python -m pytest -p no:cacheprovider --rootdir /app -c /tmp/aiforge_pytest.ini"
    )
    name = f"aiforge_test_{uuid.uuid4().hex[:12]}"
    cmd = [
        docker_exe() or "docker", "run", "--rm", "--name", name,
        "-v", f"{project_path}:/app",
        "-v", f"{PIP_CACHE_VOLUME}:/root/.cache/pip",
        "-w", "/app",
        "--memory", "2g", "--cpus", "2",
        "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", "PYTHONUNBUFFERED=1",
        IMAGE, "sh", "-c", script,
    ]
    started = time.perf_counter()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        subprocess.run([cmd[0], "rm", "-f", name], capture_output=True)
        return ExecutionResult(status=ExecutionStatus.TIMEOUT, exit_code=-1, timed_out=True,
                               stderr=f"Tests did not finish within {timeout_seconds:.0f}s in the Docker sandbox.",
                               language="python", execution_type=ExecutionType.PROJECT_TEST.value)

    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    if proc.returncode == 3:
        status = ExecutionStatus.INFRASTRUCTURE_ERROR
    elif proc.returncode == 0:
        status = ExecutionStatus.PASS
    else:
        status = ExecutionStatus.FAIL
    return ExecutionResult(
        status=status, exit_code=proc.returncode,
        stdout=proc.stdout[-200_000:], stderr=proc.stderr[-50_000:],
        duration_ms=duration_ms, language="python", execution_type=ExecutionType.PROJECT_TEST.value,
    )
