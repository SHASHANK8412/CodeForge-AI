"""
Docker sandbox for running untrusted, LLM-generated projects.

Why a container and not a subprocess
------------------------------------
Generated code is untrusted: it can delete files, read credentials, open
sockets or fork-bomb. Stripping environment variables (what the local
``SandboxExecutor`` does) does not stop any of that. The container below does:

=====================  =====================================================
Flag                   Threat it addresses
=====================  =====================================================
``--network none``     data exfiltration, downloading payloads, calling APIs
``--read-only``        writes outside the project copy / tmpfs
``--tmpfs /tmp``       gives tools scratch space without a writable rootfs
``--memory/--cpus``    memory bombs, CPU starvation of the host
``--pids-limit``       fork bombs
``--user 10001``       running as root inside the container
``--cap-drop ALL``     raw sockets, mounts, chown and other kernel capabilities
``no-new-privileges``  setuid escalation
host-side timeout      infinite loops / servers that never exit (``docker kill``)
=====================  =====================================================

The project is mounted from a *throwaway copy*, so a run can never modify the
generator's output on the host. Dependencies are pre-installed in the image
(see ``sandbox/Dockerfile``) because the network is off at run time.

Select it with ``AIFORGE_SANDBOX=docker``. If Docker is unavailable the caller
gets ``available() == False`` and should fall back (and record that it did).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_IMAGE = os.environ.get("AIFORGE_SANDBOX_IMAGE", "aiforge-sandbox:py311")
SANDBOX_USER = "10001:10001"
WORKDIR = "/work"


@dataclass
class SandboxResult:
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    timed_out: bool
    backend: str  # "docker" | "local"
    command: List[str] = field(default_factory=list)


@dataclass
class DockerLimits:
    timeout_seconds: float = 60.0
    memory_mb: int = 512
    cpus: float = 1.0
    pids: int = 256
    max_output_bytes: int = 50_000


def sandbox_backend() -> str:
    return os.environ.get("AIFORGE_SANDBOX", "local").strip().lower()


class DockerSandbox:
    def __init__(self, image: str = DEFAULT_IMAGE, docker_bin: Optional[str] = None):
        self.image = image
        self.docker = docker_bin or shutil.which("docker") or "docker"

    # ------------------------------------------------------------------ #
    def available(self) -> bool:
        """True if the docker daemon answers and the sandbox image exists."""
        try:
            info = subprocess.run([self.docker, "image", "inspect", self.image],
                                  capture_output=True, text=True, timeout=15)
            return info.returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False

    def build_argv(self, name: str, mount_dir: str, command: List[str],
                   limits: DockerLimits, env: Optional[Dict[str, str]] = None) -> List[str]:
        argv = [
            self.docker, "run", "--rm", "--name", name,
            "--network", "none",
            "--read-only",
            "--tmpfs", "/tmp:rw,size=64m",
            "--memory", f"{limits.memory_mb}m",
            "--memory-swap", f"{limits.memory_mb}m",
            "--cpus", str(limits.cpus),
            "--pids-limit", str(limits.pids),
            "--user", SANDBOX_USER,
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "-e", "PYTHONDONTWRITEBYTECODE=1",
            "-e", "HOME=/tmp",
            "-e", f"PYTHONPATH={WORKDIR}:{WORKDIR}/backend",
            "-v", f"{mount_dir}:{WORKDIR}:rw",
            "-w", WORKDIR,
        ]
        for key, value in (env or {}).items():
            argv += ["-e", f"{key}={value}"]
        argv.append(self.image)
        argv += command
        return argv

    def run(self, project_dir: str, command: List[str],
            limits: Optional[DockerLimits] = None,
            env: Optional[Dict[str, str]] = None,
            keep_copy: Optional[str] = None) -> SandboxResult:
        """Runs ``command`` against a copy of ``project_dir``.

        ``keep_copy`` lets the caller pass its own scratch dir (so it can read
        files the run produced, e.g. a JUnit XML report). Otherwise a temp copy
        is created and deleted.
        """
        limits = limits or DockerLimits()
        name = f"aiforge-sbx-{uuid.uuid4().hex[:12]}"
        tmp_root = None
        if keep_copy:
            mount_dir = keep_copy
        else:
            tmp_root = tempfile.mkdtemp(prefix="aiforge_docker_")
            mount_dir = os.path.join(tmp_root, "work")
            shutil.copytree(project_dir, mount_dir)
        # The container runs as an unprivileged uid; let it write to its copy only.
        _make_world_writable(mount_dir)

        argv = self.build_argv(name, mount_dir, command, limits, env)
        start = time.perf_counter()
        try:
            proc = subprocess.run(argv, capture_output=True, text=True,
                                  timeout=limits.timeout_seconds)
            timed_out = False
            code, out, err = proc.returncode, proc.stdout or "", proc.stderr or ""
        except subprocess.TimeoutExpired as exc:
            subprocess.run([self.docker, "kill", name], capture_output=True, timeout=15)
            timed_out = True
            code = 124
            out = _to_text(exc.stdout)
            err = _to_text(exc.stderr) + f"\n[sandbox] killed after {limits.timeout_seconds}s"
        finally:
            if tmp_root:
                shutil.rmtree(tmp_root, ignore_errors=True)

        return SandboxResult(
            exit_code=code,
            stdout=_truncate(out, limits.max_output_bytes),
            stderr=_truncate(err, limits.max_output_bytes),
            duration_ms=round((time.perf_counter() - start) * 1000, 1),
            timed_out=timed_out,
            backend="docker",
            command=command,
        )


def _make_world_writable(root: str) -> None:
    for dirpath, dirnames, filenames in os.walk(root):
        os.chmod(dirpath, 0o777)
        for fn in filenames:
            try:
                os.chmod(os.path.join(dirpath, fn), 0o666)
            except OSError:
                pass


def _to_text(data: object) -> str:
    if data is None:
        return ""
    if isinstance(data, bytes):
        return data.decode("utf-8", errors="replace")
    return str(data)


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit] + "\n[OUTPUT_LIMIT_EXCEEDED]"


def run_local(project_dir: str, command: List[str], timeout_seconds: float = 60.0,
              max_output_bytes: int = 50_000, env: Optional[Dict[str, str]] = None) -> SandboxResult:
    """Unisolated fallback: a subprocess on the host with secrets stripped.

    Use only for trusted fixtures or when Docker is unavailable. Results record
    ``backend="local"`` so reports can say the code was not isolated.
    """
    from backend.execution.sandbox_executor import global_sandbox_executor

    base_env = global_sandbox_executor._build_isolated_environment()
    base_env.update(env or {})
    env = base_env
    root = os.path.abspath(project_dir)
    env["PYTHONPATH"] = os.pathsep.join([root, os.path.join(root, "backend")])
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    start = time.perf_counter()
    try:
        proc = subprocess.run(command, cwd=root, capture_output=True, text=True,
                              timeout=timeout_seconds, env=env)
        code, out, err, timed_out = proc.returncode, proc.stdout or "", proc.stderr or "", False
    except subprocess.TimeoutExpired as exc:
        code, out, timed_out = 124, _to_text(exc.stdout), True
        err = _to_text(exc.stderr) + f"\n[sandbox] killed after {timeout_seconds}s"
    return SandboxResult(
        exit_code=code,
        stdout=_truncate(out, max_output_bytes),
        stderr=_truncate(err, max_output_bytes),
        duration_ms=round((time.perf_counter() - start) * 1000, 1),
        timed_out=timed_out,
        backend="local",
        command=command,
    )


global_docker_sandbox = DockerSandbox()


def python_in_sandbox() -> str:
    """Interpreter name to use in commands: the image's python, or the host's."""
    import sys
    return "python" if sandbox_backend() == "docker" else sys.executable


def run_sandboxed(project_dir: str, command: List[str], timeout_seconds: float = 60.0,
                  memory_mb: int = 512, keep_copy: Optional[str] = None,
                  env: Optional[Dict[str, str]] = None) -> SandboxResult:
    """Runs in Docker when ``AIFORGE_SANDBOX=docker`` and Docker is ready, else locally.

    With ``AIFORGE_SANDBOX=docker`` and no usable Docker this raises instead of
    silently running untrusted code on the host.
    """
    if sandbox_backend() == "docker":
        if not global_docker_sandbox.available():
            raise RuntimeError(
                f"AIFORGE_SANDBOX=docker but image '{global_docker_sandbox.image}' is not available. "
                "Build it with: docker build -t aiforge-sandbox:py311 sandbox/"
            )
        return global_docker_sandbox.run(project_dir, command,
                                         DockerLimits(timeout_seconds=timeout_seconds, memory_mb=memory_mb),
                                         env=env, keep_copy=keep_copy)
    return run_local(keep_copy or project_dir, command, timeout_seconds=timeout_seconds, env=env)


__all__ = [
    "DockerSandbox", "DockerLimits", "SandboxResult", "global_docker_sandbox",
    "run_local", "run_sandboxed", "sandbox_backend", "python_in_sandbox", "Path",
]
