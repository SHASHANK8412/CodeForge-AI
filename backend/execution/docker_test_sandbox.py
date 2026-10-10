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


def _docker(*args: str, timeout: float) -> subprocess.CompletedProcess:
    return subprocess.run([docker_exe() or "docker", *args], capture_output=True, text=True, timeout=timeout)


def run_pytest_in_docker(project_path: Path, timeout_seconds: float = 900.0) -> ExecutionResult:
    """
    Two containers, so generated code never runs with network access or as root:
    1. install: network on, installs requirements + pytest into a throwaway volume (pip cache shared)
    2. test:    --network none, non-root user, CPU/memory/process limits, deps volume read-only
    """
    project_path = Path(project_path).resolve()
    req = requirements_file(project_path)
    req_rel = req.relative_to(project_path).as_posix() if req else None
    run_id = uuid.uuid4().hex[:12]
    deps_volume = f"aiforge_deps_{run_id}"
    names = [f"aiforge_install_{run_id}", f"aiforge_test_{run_id}"]
    started = time.perf_counter()

    def result(status, code, out="", err="", timed_out=False):
        return ExecutionResult(status=status, exit_code=code, stdout=out[-200_000:], stderr=err[-50_000:],
                               timed_out=timed_out, duration_ms=round((time.perf_counter() - started) * 1000, 2),
                               language="python", execution_type=ExecutionType.PROJECT_TEST.value)

    install = ("pip install -q --disable-pip-version-check --root-user-action=ignore --target /deps "
               + (f"-r /app/{req_rel} " if req_rel else "") + "pytest")
    try:
        inst = _docker(
            "run", "--rm", "--name", names[0],
            "-v", f"{project_path}:/app:ro", "-v", f"{deps_volume}:/deps", "-v", f"{PIP_CACHE_VOLUME}:/root/.cache/pip",
            # Package builds can run code from the project's requirements: no capabilities either.
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "256",
            "--memory", "2g", "--cpus", "2", IMAGE,
            "sh", "-c", f"{install} > /tmp/pip.log 2>&1 || {{ tail -40 /tmp/pip.log; exit 3; }}; chmod -R a+rX /deps",
            timeout=timeout_seconds,
        )
        if inst.returncode != 0:
            return result(ExecutionStatus.INFRASTRUCTURE_ERROR, 3, inst.stdout,
                          "Dependency install failed in the Docker sandbox:\n" + inst.stdout + inst.stderr)

        remaining = max(30.0, timeout_seconds - (time.perf_counter() - started))
        test = _docker(
            "run", "--rm", "--name", names[1],
            "--network", "none", "--user", "1000:1000",
            "--memory", "2g", "--cpus", "2", "--pids-limit", "256", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "-v", f"{project_path}:/app", "-v", f"{deps_volume}:/deps:ro", "-w", "/app",
            "-e", "PYTHONPATH=/deps", "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", "PYTHONUNBUFFERED=1",
            "-e", "HOME=/tmp",
            IMAGE, "sh", "-c",
            "printf '[pytest]\n' > /tmp/aiforge_pytest.ini; "
            "python -m pytest -p no:cacheprovider --rootdir /app -c /tmp/aiforge_pytest.ini",
            timeout=remaining,
        )
    except subprocess.TimeoutExpired:
        return result(ExecutionStatus.TIMEOUT, -1,
                      err=f"Tests did not finish within {timeout_seconds:.0f}s in the Docker sandbox.", timed_out=True)
    finally:
        for name in names:
            subprocess.run([docker_exe() or "docker", "rm", "-f", name], capture_output=True)
        subprocess.run([docker_exe() or "docker", "volume", "rm", "-f", deps_volume], capture_output=True)

    status = ExecutionStatus.PASS if test.returncode == 0 else ExecutionStatus.FAIL
    return result(status, test.returncode, test.stdout, test.stderr)
