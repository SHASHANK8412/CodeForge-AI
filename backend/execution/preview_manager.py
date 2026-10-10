"""
AIForge Live Preview Manager - generated apps run only inside hardened Docker containers.

Generated code is untrusted, so a preview never runs it on the host (this module used to start
it as host processes and install its dependencies into the host environment):
  1. install - dependencies go into a throwaway volume (network on, no capabilities, process limit)
  2. run     - non-root user, all capabilities dropped, no-new-privileges, CPU/memory/process
               limits, read-only root filesystem, project mounted read-only and copied into the
               container's tmpfs, the port published on 127.0.0.1 only, and the server stops
               itself after AIFORGE_PREVIEW_TTL seconds.
A frontend with a build script is built in a node container and served read-only the same way.

A service is reported "running" only after an HTTP probe gets an answer from it; otherwise it is
"failed" with the container's logs. Without a Docker daemon the status is "unavailable" - there
is no host fallback.

AIFORGE_PREVIEW: "docker" (default) or "off".
"""

import ast
import json
import logging
import os
import subprocess
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from backend.execution.docker_test_sandbox import IMAGE, PIP_CACHE_VOLUME, docker_available, docker_exe
from backend.execution.project_env import requirements_file

_logger = logging.getLogger("aiforge.execution.preview_manager")

NODE_IMAGE = os.environ.get("AIFORGE_PREVIEW_NODE_IMAGE", "node:22-slim")
STARTUP_TIMEOUT = float(os.environ.get("AIFORGE_PREVIEW_STARTUP_SECONDS", "60"))
PROBE_PATHS = ("/health", "/docs", "/")
HARDENING = [
    "--user", "1000:1000", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
    "--memory", "1g", "--cpus", "1", "--pids-limit", "128", "--read-only", "--tmpfs", "/tmp:rw,size=256m",
]


def preview_ttl() -> int:
    return int(os.environ.get("AIFORGE_PREVIEW_TTL", "1800"))


def preview_enabled() -> bool:
    return os.environ.get("AIFORGE_PREVIEW", "docker").strip().lower() != "off"


@dataclass
class ServicePreview:
    status: str = "not_started"   # not_started | installing | building | starting | running | failed | not_previewable
    url: Optional[str] = None
    probe: Optional[str] = None   # "GET /health -> 200" once verified
    error: Optional[str] = None
    logs: str = ""
    container: Optional[str] = None


@dataclass
class Preview:
    project_id: str
    status: str = "starting"      # starting | running | partial | failed | stopped | unavailable
    backend: ServicePreview = field(default_factory=ServicePreview)
    frontend: ServicePreview = field(default_factory=ServicePreview)
    started_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    reason: Optional[str] = None
    volumes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        d = asdict(self)
        d.pop("volumes", None)
        return d


_previews: Dict[str, Preview] = {}
_lock = threading.Lock()


def _docker(*args: str, timeout: float = 60) -> subprocess.CompletedProcess:
    return subprocess.run([docker_exe() or "docker", *args], capture_output=True, text=True, timeout=timeout)


# --- What to run ------------------------------------------------------------------------------

def backend_entry(project: Path) -> Optional[Dict[str, str]]:
    """The ASGI app to serve: (working dir inside /app, module:attribute), or None."""
    for rel, workdir, module in (("backend/main.py", "backend", "main:app"), ("main.py", ".", "main:app"),
                                 ("app/main.py", ".", "app.main:app"), ("src/main.py", "src", "main:app")):
        path = project / rel
        if not path.is_file():
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            return None
        defines_app = any(
            isinstance(n, (ast.Assign, ast.AnnAssign)) and any(
                isinstance(t, ast.Name) and t.id == "app"
                for t in (n.targets if isinstance(n, ast.Assign) else [n.target]))
            for n in tree.body)
        if defines_app:
            return {"workdir": workdir, "module": module}
    return None


def frontend_entry(project: Path) -> Optional[str]:
    """The folder of a buildable frontend (package.json with a build script), relative to the project."""
    for rel in ("frontend", "."):
        pkg = project / rel / "package.json"
        if pkg.is_file():
            try:
                if "build" in (json.loads(pkg.read_text(encoding="utf-8")).get("scripts") or {}):
                    return rel
            except (ValueError, OSError):
                return None
    return None


def backend_commands(project: Path, run_id: str, entry: Dict[str, str], ttl: int) -> Dict[str, List[str]]:
    """docker argv for the install and run containers (no generated code runs during install)."""
    req = requirements_file(project)
    req_arg = f"-r /app/{req.relative_to(project).as_posix()} " if req else ""
    deps = f"aiforge_preview_deps_{run_id}"
    install = [
        "run", "--rm", "--name", f"aiforge_preview_install_{run_id}",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "256",
        "--memory", "2g", "--cpus", "2",
        "-v", f"{project}:/app:ro", "-v", f"{deps}:/deps", "-v", f"{PIP_CACHE_VOLUME}:/root/.cache/pip",
        IMAGE, "sh", "-c",
        f"pip install -q --disable-pip-version-check --root-user-action=ignore --target /deps {req_arg}uvicorn"
        " > /tmp/pip.log 2>&1 || { tail -40 /tmp/pip.log; exit 3; }; chmod -R a+rX /deps",
    ]
    # The project is mounted read-only and copied into the container's tmpfs, so an app that
    # writes next to itself (a SQLite file, uploads) works without touching the host copy.
    workdir = "/tmp/app" if entry["workdir"] == "." else f"/tmp/app/{entry['workdir']}"
    run = [
        "run", "-d", "--name", f"aiforge_preview_be_{run_id}", "--label", "aiforge.preview=1",
        *HARDENING, "-p", "127.0.0.1::8000",
        "-v", f"{project}:/app:ro", "-v", f"{deps}:/deps:ro",
        "-e", f"PYTHONPATH=/deps:{workdir}:/tmp/app", "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", "PYTHONUNBUFFERED=1",
        "-e", "HOME=/tmp",
        IMAGE, "sh", "-c",
        "mkdir -p /tmp/app && tar -C /app --exclude=./.venv --exclude=./frontend/node_modules --exclude=./node_modules "
        f"-cf - . | tar -C /tmp/app -xf - && cd {workdir} && "
        f"exec timeout {ttl} python -m uvicorn {entry['module']} --host 0.0.0.0 --port 8000",
    ]
    return {"install": install, "run": run, "volume": deps}


def frontend_commands(project: Path, run_id: str, rel: str, ttl: int, api_url: Optional[str]) -> Dict[str, List[str]]:
    """Build in a node container (network on, no capabilities), serve the static output read-only."""
    src = project if rel == "." else project / rel
    build = [
        "run", "--rm", "--name", f"aiforge_preview_build_{run_id}",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "512",
        "--memory", "2g", "--cpus", "2", "-e", "HOME=/tmp", "-e", "npm_config_cache=/tmp/npm",
        *(["-e", f"VITE_API_URL={api_url}", "-e", f"REACT_APP_API_URL={api_url}"] if api_url else []),
        "-v", f"{src}:/src:ro", "-v", f"aiforge_preview_site_{run_id}:/out", NODE_IMAGE, "sh", "-c",
        "cp -r /src /tmp/app && cd /tmp/app && rm -rf node_modules && "
        "npm install --no-audit --no-fund --loglevel=error && npm run build && "
        "for d in dist build out; do if [ -d \"$d\" ]; then cp -r \"$d\"/. /out/; exit 0; fi; done; "
        "echo 'build produced no dist/ build/ or out/ folder'; exit 4",
    ]
    serve = [
        "run", "-d", "--name", f"aiforge_preview_fe_{run_id}", "--label", "aiforge.preview=1",
        *HARDENING, "-p", "127.0.0.1::8080",
        "-v", f"aiforge_preview_site_{run_id}:/site:ro",
        IMAGE, "timeout", str(ttl), "python", "-m", "http.server", "8080", "--directory", "/site",
    ]
    return {"build": build, "run": serve, "volume": f"aiforge_preview_site_{run_id}"}


# --- Running and verifying ---------------------------------------------------------------------

def _host_port(container: str, port: int) -> Optional[int]:
    out = _docker("port", container, str(port), timeout=20).stdout.strip().splitlines()
    for line in out:
        if line.startswith("127.0.0.1:"):
            return int(line.rsplit(":", 1)[1])
    return None


def _logs(container: str) -> str:
    res = _docker("logs", "--tail", "120", container, timeout=20)
    return (res.stdout + res.stderr)[-12_000:]


def _probe(url: str, timeout: float) -> Optional[str]:
    """First probe path that answers below 500, as 'GET /path -> code'; None if nothing answered."""
    import httpx
    deadline = time.time() + timeout
    while time.time() < deadline:
        for path in PROBE_PATHS:
            try:
                res = httpx.get(url + path, timeout=3.0)
                if res.status_code < 500:
                    return f"GET {path} -> {res.status_code}"
            except httpx.HTTPError:
                pass
        time.sleep(1.0)
    return None


def _start_service(svc: ServicePreview, run_cmd: List[str], port: int) -> None:
    started = _docker(*run_cmd, timeout=120)
    if started.returncode != 0:
        svc.status, svc.error = "failed", (started.stderr or started.stdout)[-2000:]
        return
    svc.container = run_cmd[run_cmd.index("--name") + 1]
    host_port = _host_port(svc.container, port)
    if not host_port:
        svc.status, svc.error, svc.logs = "failed", "the container exited before its port was published", _logs(svc.container)
        return
    url = f"http://127.0.0.1:{host_port}"
    svc.status = "starting"
    probe = _probe(url, STARTUP_TIMEOUT)
    svc.logs = _logs(svc.container)
    if probe:
        svc.status, svc.url, svc.probe = "running", url, probe
    else:
        svc.status = "failed"
        svc.error = f"no HTTP answer on {', '.join(PROBE_PATHS)} within {STARTUP_TIMEOUT:.0f}s"


def _run_preview(preview: Preview, project: Path) -> None:
    run_id = uuid.uuid4().hex[:10]
    ttl = preview_ttl()
    preview.expires_at = time.time() + ttl
    be_entry, fe_rel = backend_entry(project), frontend_entry(project)
    if not be_entry and not fe_rel:
        preview.status = "failed"
        preview.reason = "nothing to preview: no FastAPI app (main.py defining `app`) and no frontend with a build script"
        return

    if be_entry:
        cmds = backend_commands(project, run_id, be_entry, ttl)
        preview.volumes.append(cmds["volume"])
        preview.backend.status = "installing"
        inst = _docker(*cmds["install"], timeout=900)
        if inst.returncode != 0:
            preview.backend.status = "failed"
            preview.backend.error = "dependency install failed"
            preview.backend.logs = (inst.stdout + inst.stderr)[-12_000:]
        else:
            _start_service(preview.backend, cmds["run"], 8000)
    else:
        preview.backend.status = "not_previewable"
        preview.backend.error = "no FastAPI app found (main.py defining `app`)"

    if fe_rel:
        cmds = frontend_commands(project, run_id, fe_rel, ttl, preview.backend.url)
        preview.volumes.append(cmds["volume"])
        preview.frontend.status = "building"
        built = _docker(*cmds["build"], timeout=1200)
        if built.returncode != 0:
            preview.frontend.status = "failed"
            preview.frontend.error = "frontend build failed"
            preview.frontend.logs = (built.stdout + built.stderr)[-12_000:]
        else:
            _start_service(preview.frontend, cmds["run"], 8080)
    else:
        preview.frontend.status = "not_previewable"
        preview.frontend.error = "no package.json with a build script"

    services = [s for s in (preview.backend, preview.frontend) if s.status != "not_previewable"]
    running = [s for s in services if s.status == "running"]
    preview.status = "running" if running and len(running) == len(services) else "partial" if running else "failed"


def start_preview(project_id: str, project_dir: Path, wait: bool = False) -> Preview:
    """Start (or restart) a project's preview. Returns at once unless wait=True."""
    project = Path(project_dir).resolve()
    stop_preview(project_id)
    preview = Preview(project_id=project_id)
    with _lock:
        _previews[project_id] = preview
    if not preview_enabled():
        preview.status, preview.reason = "unavailable", "previews are disabled (AIFORGE_PREVIEW=off)"
        return preview
    if not docker_available():
        preview.status = "unavailable"
        preview.reason = "Docker is not running; generated apps are only ever started inside containers"
        return preview

    def work():
        try:
            _run_preview(preview, project)
        except Exception as e:  # noqa: BLE001 - reported on the preview, never raised into the caller
            _logger.exception("Preview for %s failed", project_id)
            preview.status, preview.reason = "failed", f"{type(e).__name__}: {e}"

    if wait:
        work()
    else:
        threading.Thread(target=work, name=f"preview-{project_id}", daemon=True).start()
    return preview


def get_preview(project_id: str, refresh_logs: bool = True) -> Optional[Preview]:
    with _lock:
        preview = _previews.get(project_id)
    if preview and refresh_logs:
        for svc in (preview.backend, preview.frontend):
            if svc.container and svc.status == "running":
                svc.logs = _logs(svc.container)
                if not _docker("inspect", "-f", "{{.State.Running}}", svc.container, timeout=20).stdout.strip() == "true":
                    svc.status, svc.error = "failed", "the container has stopped (crashed or reached its time limit)"
    return preview


def stop_preview(project_id: str) -> bool:
    with _lock:
        preview = _previews.get(project_id)
    if not preview:
        return False
    for svc in (preview.backend, preview.frontend):
        if svc.container:
            _docker("rm", "-f", svc.container, timeout=60)
            if svc.status == "running":
                svc.status = "stopped"
    for vol in preview.volumes:
        _docker("volume", "rm", "-f", vol, timeout=60)
    preview.volumes = []
    preview.status = "stopped"
    return True


class PreviewManager:
    """Facade kept for existing callers (routes, tests): one preview per project id."""

    async def start_preview_async(self, project_id: str, project_path: Path,
                                  files_manifest: Optional[Dict[str, str]] = None) -> Preview:
        """Start a preview and wait until it is verified or has failed."""
        import asyncio
        return await asyncio.to_thread(start_preview, project_id, project_path, True)

    def start_preview(self, project_id: str, project_path: Path, wait: bool = False) -> Preview:
        return start_preview(project_id, project_path, wait)

    def stop_preview(self, project_id: str) -> bool:
        return stop_preview(project_id)

    def get_session(self, project_id: str) -> Optional[Preview]:
        return get_preview(project_id)


global_preview_manager = PreviewManager()
