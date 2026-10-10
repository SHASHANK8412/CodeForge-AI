"""
Run a generated project's tests or build inside throwaway Docker containers.

The containers see only the project folder (mounted read-only), install the project's own
dependencies (pip with a shared cache, or npm), and then run pytest / the npm script with no
network and no capabilities. Nothing is installed on the host, and the generated code never runs
in AIForge's process or environment.

Mode (AIFORGE_TEST_SANDBOX): "auto" (default) and "docker" run generated code only in Docker - when
Docker is not available the run is reported as not run, never moved to the host; "local" is an
explicit opt-in to run it on this machine (per-project venv), meant for AIForge's own test suite.
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


def docker_env() -> dict:
    """Environment for docker calls: Docker's own bin folder on PATH, so the CLI finds its
    credential helper (docker-credential-desktop) when it has to pull an image."""
    env = dict(os.environ)
    exe = docker_exe()
    if exe:
        env["PATH"] = str(Path(exe).parent) + os.pathsep + env.get("PATH", "")
    return env


def _docker(*args: str, timeout: float) -> subprocess.CompletedProcess:
    return subprocess.run([docker_exe() or "docker", *args], capture_output=True, text=True, timeout=timeout,
                          env=docker_env())


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


NODE_IMAGE = os.environ.get("AIFORGE_NODE_IMAGE", "node:22-slim")


def npm_commands(project_path: Path, run_id: str, script: str) -> dict:
    """docker argv for the npm install container (network on) and the script container (no network)."""
    work = f"aiforge_npm_{run_id}"
    caps = ["--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--memory", "2g", "--cpus", "2"]
    install = [
        "run", "--rm", "--name", f"aiforge_npm_install_{run_id}", *caps, "--pids-limit", "512",
        "-e", "npm_config_cache=/tmp/npm", "-v", f"{project_path}:/src:ro", "-v", f"{work}:/work", NODE_IMAGE,
        "sh", "-c", "cp -r /src/. /work && cd /work && rm -rf node_modules .venv && "
                    "npm install --no-audit --no-fund --loglevel=error",
    ]
    run = [
        "run", "--rm", "--name", f"aiforge_npm_run_{run_id}", *caps, "--pids-limit", "256", "--network", "none",
        "-e", "CI=true", "-v", f"{work}:/work", "-w", "/work", NODE_IMAGE, "npm", "run", script, "--silent",
    ]
    return {"install": install, "run": run, "volume": work}


def run_npm_in_docker(project_path: Path, script: str, timeout_seconds: float = 900.0) -> ExecutionResult:
    """`npm run <script>` (build or test) for a generated JS project, in two throwaway containers."""
    project_path = Path(project_path).resolve()
    cmds = npm_commands(project_path, uuid.uuid4().hex[:12], script)
    started = time.perf_counter()

    def result(status, code, out="", err="", timed_out=False):
        return ExecutionResult(status=status, exit_code=code, stdout=out[-200_000:], stderr=err[-50_000:],
                               timed_out=timed_out, duration_ms=round((time.perf_counter() - started) * 1000, 2),
                               language="javascript", execution_type=ExecutionType.PROJECT_TEST.value)
    try:
        inst = _docker(*cmds["install"], timeout=timeout_seconds)
        if inst.returncode != 0:
            return result(ExecutionStatus.INFRASTRUCTURE_ERROR, 3, inst.stdout,
                          "npm install failed in the Docker sandbox:\n" + inst.stdout + inst.stderr)
        run = _docker(*cmds["run"], timeout=max(30.0, timeout_seconds - (time.perf_counter() - started)))
    except subprocess.TimeoutExpired:
        return result(ExecutionStatus.TIMEOUT, -1, err=f"npm run {script} did not finish within {timeout_seconds:.0f}s.",
                      timed_out=True)
    finally:
        subprocess.run([docker_exe() or "docker", "volume", "rm", "-f", cmds["volume"]], capture_output=True, env=docker_env())
    return result(ExecutionStatus.PASS if run.returncode == 0 else ExecutionStatus.FAIL, run.returncode, run.stdout, run.stderr)


def not_run_result(language: str) -> ExecutionResult:
    """Docker is required for generated code and is not available: the run did not happen."""
    return ExecutionResult(
        status=ExecutionStatus.INFRASTRUCTURE_ERROR, exit_code=-1, language=language,
        execution_type=ExecutionType.PROJECT_TEST.value,
        stderr=("Not run: generated code only runs in the Docker sandbox, and Docker is not available. "
                "Start Docker, or set AIFORGE_TEST_SANDBOX=local to allow running it on this machine."),
    )
