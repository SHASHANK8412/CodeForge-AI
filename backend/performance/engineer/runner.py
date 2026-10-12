"""
Controlled workload runs of a FastAPI app inside the preview sandbox.

For each version of the project (the baseline, and for a comparison the candidate):
  1. dependencies are installed into a throwaway volume (no project code runs during install)
  2. the app starts in the hardened preview container (non-root, no capabilities, CPU 1 /
     memory 1 GB / 128 processes, read-only root, port on 127.0.0.1 only, time limit)
  3. readiness = the first successful answer from the health path (or /health, /docs, /)
  4. warm-up requests, then the workload's repetitions; container CPU and memory are sampled
     with `docker stats` while it runs
When two versions are compared they run side by side and their repetitions alternate
(A B A B ...) so drift on the machine affects both alike. Containers and volumes are always removed.
"""

import hashlib
import json
import logging
import os
import platform
import re
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from backend.evolution.autopilot.redact import redact
from backend.performance.engineer.models import Endpoint, Environment, Measurement, Resources, Workload
from backend.performance.engineer.workload import run_endpoint, summarize, warm_up

_logger = logging.getLogger("aiforge.performance.runner")
RUN_DEADLINE_SECONDS = float(os.environ.get("AIFORGE_PERF_DEADLINE_SECONDS", "1500"))
CONTAINER_TTL_SECONDS = 1800
READY_TIMEOUT_SECONDS = 90.0


class Cancelled(Exception):
    pass


def _mb(text: str) -> Optional[float]:
    m = re.match(r"\s*([\d.]+)\s*([KMG]i?B|B)", text or "")
    if not m:
        return None
    value, unit = float(m.group(1)), m.group(2)
    return round(value * {"B": 1 / 1048576, "KiB": 1 / 1024, "KB": 1 / 1024, "MiB": 1, "MB": 1,
                           "GiB": 1024, "GB": 1024}[unit], 2)


def parse_docker_stats(line: str) -> Optional[Tuple[float, float]]:
    """(cpu %, memory MB) from one `docker stats --format '{{json .}}'` line."""
    try:
        data = json.loads(line)
        cpu = float(str(data.get("CPUPerc", "")).rstrip("%"))
        mem = _mb(str(data.get("MemUsage", "")).split("/")[0])
    except (ValueError, TypeError):
        return None
    return (cpu, mem) if mem is not None else None


class StatsSampler:
    """Samples a container's CPU and memory in a background thread while a workload runs."""

    def __init__(self, container: str, docker: Callable[..., object]):
        self.container, self.docker = container, docker
        self.samples: List[Tuple[float, float]] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def _loop(self):
        while not self._stop.is_set():
            res = self.docker("stats", "--no-stream", "--format", "{{json .}}", self.container, timeout=20)
            parsed = parse_docker_stats((getattr(res, "stdout", "") or "").strip().splitlines()[0]) \
                if (getattr(res, "stdout", "") or "").strip() else None
            if parsed:
                self.samples.append(parsed)
            self._stop.wait(0.2)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self._thread.join(timeout=30)


def resources_of(samples: List[Tuple[float, float]]) -> Resources:
    if not samples:
        return Resources(samples=0, method="docker stats returned no samples (not measured)")
    cpu = [c for c, _ in samples]
    mem = [m for _, m in samples]
    return Resources(samples=len(samples), cpu_avg_pct=round(sum(cpu) / len(cpu), 2), cpu_max_pct=round(max(cpu), 2),
                     mem_avg_mb=round(sum(mem) / len(mem), 2), mem_max_mb=round(max(mem), 2))


def environment(workload: Workload) -> Environment:
    from backend.execution.docker_test_sandbox import IMAGE
    from backend.execution.preview_manager import HARDENING
    limits = {HARDENING[i].lstrip("-"): HARDENING[i + 1] for i in range(len(HARDENING) - 1)
              if HARDENING[i] in ("--memory", "--cpus", "--pids-limit")}
    return Environment(
        method="the app runs in a Docker container; requests are sent from the AIForge host to 127.0.0.1",
        image=IMAGE, limits=limits,
        load_generator=f"httpx, {workload.concurrency} worker thread(s) with keep-alive; latency = wall-clock per request",
        host={"platform": platform.platform(), "python": platform.python_version(), "cpu_count": os.cpu_count()},
        notes=[f"{workload.warmup_requests} warm-up request(s) per endpoint, not measured",
               f"{workload.repetitions} repetition(s) of up to {workload.requests_per_endpoint} request(s) or "
               f"{workload.max_seconds_per_endpoint:.0f}s per endpoint, whichever comes first (the count actually sent is reported)"],
    )


class _App:
    def __init__(self, label: str, project: Path):
        self.label, self.project = label, project
        self.container: Optional[str] = None
        self.url: Optional[str] = None
        self.run_cmd: List[str] = []
        self.measurement = Measurement(label=label)
        self.reps: Dict[str, list] = {}
        self.samples: List[Tuple[float, float]] = []


def _requirements_key(project: Path) -> str:
    from backend.execution.project_env import requirements_file
    req = requirements_file(project)
    return hashlib.sha1(req.read_bytes()).hexdigest() if req else "none"


def measure(projects: Dict[str, Path], workload: Workload, should_stop: Optional[Callable[[], bool]] = None,
            on_stage: Optional[Callable[[str, str], None]] = None, resources: Optional[Dict[str, Any]] = None,
            drive: Optional[Callable[[str, Callable[[], bool]], Dict[str, Any]]] = None
            ) -> Tuple[Dict[str, Measurement], Environment]:
    """Run `workload` against each project version. Returns {label: Measurement} and the environment.
    `resources` sets the app container's CPU / memory / workers; `drive(url, stop)` replaces the workload with
    the caller's own traffic (its result is stored in Measurement.custom; CPU and memory are still sampled)."""
    from backend.execution.docker_test_sandbox import docker_available
    from backend.execution.preview_manager import (_docker, _host_port, _logs, backend_commands, backend_entry,
                                                   backend_problem)
    env = environment(workload)
    deadline = time.monotonic() + RUN_DEADLINE_SECONDS
    stop = lambda: (should_stop is not None and should_stop()) or time.monotonic() > deadline  # noqa: E731
    stage = on_stage or (lambda name, status: None)
    apps = [_App(label, Path(p).resolve()) for label, p in projects.items()]
    if not docker_available():
        for a in apps:
            a.measurement.status = "unavailable"
            a.measurement.error = "Docker is not available: apps are only run inside containers, so nothing was measured"
        return {a.label: a.measurement for a in apps}, env

    run_id = uuid.uuid4().hex[:10]
    volumes: Dict[str, str] = {}
    try:
        # 1. install (once per distinct requirements file)
        stage("install dependencies", "running")
        for a in apps:
            entry = backend_entry(a.project)
            if entry is None:
                a.measurement.status, a.measurement.error = "unavailable", f"not a supported FastAPI app: {backend_problem(a.project)}"
                continue
            key = _requirements_key(a.project)
            cmds = backend_commands(a.project, f"{run_id}_{a.label}", entry, CONTAINER_TTL_SECONDS, resources)
            if key not in volumes:
                inst = _docker(*cmds["install"], timeout=900)
                if inst.returncode != 0:
                    a.measurement.status = "failed"
                    a.measurement.error = "dependency install failed"
                    a.measurement.logs_tail = redact((inst.stdout + inst.stderr)[-3000:])
                    continue
                volumes[key] = cmds["volume"]
            # every version runs against the dependency volume of its own requirements file
            a.run_cmd = [f"{volumes[key]}:/deps:ro" if arg == f"{cmds['volume']}:/deps:ro" else arg for arg in cmds["run"]]
        stage("install dependencies", "done")
        if stop():
            raise Cancelled()

        # 2. start and wait for readiness
        stage("start and readiness check", "running")
        for a in apps:
            if a.measurement.status != "pending":
                continue
            began = time.perf_counter()
            started = _docker(*a.run_cmd, timeout=120)
            if started.returncode != 0:
                a.measurement.status, a.measurement.error = "failed", redact((started.stderr or started.stdout)[-1500:])
                continue
            a.container = a.run_cmd[a.run_cmd.index("--name") + 1]
            port = _host_port(a.container, 8000)
            if not port:
                a.measurement.status, a.measurement.error = "failed", "the container exited before its port was published"
                a.measurement.logs_tail = redact(_logs(a.container)[-3000:])
                continue
            a.url = f"http://127.0.0.1:{port}"
            probe = wait_ready(a.url, workload.health_path, READY_TIMEOUT_SECONDS, stop)
            if probe is None:
                a.measurement.status = "failed"
                a.measurement.error = (f"the app did not pass its readiness check within {READY_TIMEOUT_SECONDS:.0f}s "
                                       f"({workload.health_path or '/health, /docs or /'})")
                a.measurement.logs_tail = redact(_logs(a.container)[-3000:])
                continue
            a.measurement.startup_seconds = round(time.perf_counter() - began, 3)
            a.measurement.readiness_probe = probe
        stage("start and readiness check", "done")

        live = [a for a in apps if a.measurement.status == "pending"]
        if drive is not None:
            stage("workload", "running")
            for a in live:
                with StatsSampler(a.container, _docker) as sampler:
                    a.measurement.custom = drive(a.url, stop)
                a.measurement.resources = resources_of(sampler.samples)
                a.measurement.logs_tail = redact(_logs(a.container)[-2000:])
                a.measurement.status = "measured"
            stage("workload", "done")
            live = []
        if live and not workload.endpoints:
            workload.endpoints = endpoints_from_openapi(live[0].url)
            env.notes.append("endpoints taken from the app's /openapi.json: GET operations without path or "
                             "required query parameters" if workload.endpoints else
                             "the app's /openapi.json lists no GET endpoint without parameters")
        if live and not workload.endpoints:
            for a in live:
                a.measurement.status = "unavailable"
                a.measurement.error = "no endpoint to measure: give the workload explicit endpoints"
            live = []
        # 3. warm-up, then alternating repetitions
        stage("workload", "running")
        for a in live:
            warm_up(a.url, workload)
        for rep in range(workload.repetitions):
            order = live if rep % 2 == 0 else list(reversed(live))
            for a in order:
                for ep in workload.endpoints:
                    if stop():
                        raise Cancelled()
                    with StatsSampler(a.container, _docker) as sampler:
                        result = run_endpoint(a.url, ep, workload.requests_per_endpoint, workload.concurrency,
                                              workload.request_timeout_seconds, stop, workload.max_seconds_per_endpoint)
                    a.samples += sampler.samples
                    a.reps.setdefault(f"{ep.method} {ep.path}", []).append(result)
        for a in live:
            a.measurement.endpoints = [summarize(ep, a.reps.get(f"{ep.method} {ep.path}", [])) for ep in workload.endpoints]
            a.measurement.resources = resources_of(a.samples)
            a.measurement.logs_tail = redact(_logs(a.container)[-2000:])
            a.measurement.status = "measured"
        stage("workload", "done")
    except Cancelled:
        for a in apps:
            if a.measurement.status in ("pending", "measured"):
                a.measurement.status = "cancelled"
                a.measurement.error = "stopped (cancelled or the run's time limit was reached); partial data discarded"
                a.measurement.endpoints = []
    finally:
        stage("clean up", "running")
        for a in apps:
            if a.container:
                _docker("rm", "-f", a.container, timeout=60)
        for vol in volumes.values():
            _docker("volume", "rm", "-f", vol, timeout=60)
        stage("clean up", "done")
    return {a.label: a.measurement for a in apps}, env


def endpoints_from_openapi(url: str, limit: int = 5) -> List[Endpoint]:
    """GET operations without path parameters or required query parameters, from the running app."""
    import httpx
    try:
        spec = httpx.get(url + "/openapi.json", timeout=5.0).json()
    except (httpx.HTTPError, ValueError):
        return []
    out = []
    for path, ops in sorted((spec.get("paths") or {}).items()):
        op = (ops or {}).get("get")
        if not op or "{" in path or path in ("/docs", "/redoc", "/openapi.json"):
            continue
        if any(p.get("required") for p in op.get("parameters") or []):
            continue
        out.append(Endpoint(method="GET", path=path))
    return out[:limit]


def wait_ready(url: str, health_path: Optional[str], timeout: float, stop: Callable[[], bool]) -> Optional[str]:
    """'GET /path -> code' for the first successful readiness answer, or None."""
    import httpx
    paths = [health_path] if health_path else ["/health", "/docs", "/"]
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and not stop():
        for path in paths:
            try:
                code = httpx.get(url + path, timeout=3.0).status_code
            except httpx.HTTPError:
                continue
            if code < 400:
                return f"GET {path} -> {code}"
        time.sleep(0.5)
    return None
