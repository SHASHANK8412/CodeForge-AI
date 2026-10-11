"""
The isolated environment of one chaos experiment.

  network     `docker network create --internal`: containers reach each other by name and nothing
              else (no route to the host, the LAN or the internet); nothing is published on the host
  app         the project in the hardened preview container (non-root, all capabilities dropped,
              no-new-privileges, read-only root, CPU/memory/process limits, time limit), on that network only
  dependency  disposable stub services (AIForge's own code) the app reaches through an env var
  probe       a container on the same network that sends the requests and reports timings
Every container, the network and the dependency volume carry the label aiforge.chaos=<id> and are
removed by cleanup(), also after errors. Only these containers are ever stopped, restarted or paused.
"""

import json
import logging
import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.chaos.models import AssessmentConfig, Check, DependencySpec, Target
from backend.chaos.scripts import CONTROL, PROBE, STUB_DEPENDENCY
from backend.evolution.autopilot.redact import redact

_logger = logging.getLogger("aiforge.chaos.sandbox")
TTL_SECONDS = 1800
LABEL = "aiforge.chaos"
DEP_LIMITS = ["--user", "1000:1000", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--read-only",
              "--memory", "256m", "--cpus", "0.5", "--pids-limit", "64"]


class SandboxError(RuntimeError):
    pass


def _docker(*args: str, timeout: float = 60):
    from backend.execution.preview_manager import _docker as preview_docker
    return preview_docker(*args, timeout=timeout)


def preflight(project: Path, config: AssessmentConfig, scenarios_needing_dependency: List[str]) -> List[Check]:
    """Safety and feasibility checks; an experiment runs only if every one passes."""
    from backend.execution.docker_test_sandbox import docker_available
    from backend.execution.preview_manager import backend_entry, backend_problem
    checks: List[Check] = []

    def add(name, ok, detail):
        checks.append(Check(check=name, passed=bool(ok), detail=detail))

    add("environment is an isolated sandbox", config.environment == "sandbox",
        "experiments run only in a disposable Docker network created for them"
        if config.environment == "sandbox" else
        f"'{config.environment}' is refused: production and shared environments are never targeted")
    docker = docker_available()
    add("Docker is available", docker, "required to create the isolated network and containers" if docker
        else "Docker is not running: nothing can be isolated, so nothing is executed")
    entry = backend_entry(project)
    add("supported application", entry is not None,
        f"FastAPI app {entry['module']} in {entry['workdir']}" if entry else f"not runnable: {backend_problem(project)}")
    names = [d.name for d in config.dependencies]
    add("dependency names are unique", len(names) == len(set(names)), ", ".join(names) or "no dependencies")
    needs = [s for s in config.scenarios if s in scenarios_needing_dependency]
    add("dependency scenarios have a test dependency", not needs or bool(config.dependencies),
        "dependency scenarios need an explicitly configured stub dependency" if needs and not config.dependencies
        else "ok")
    add("resource limits are bounded", True,
        f"app: {config.limits.memory_mb} MB, {config.limits.cpus} CPU, 128 processes; "
        f"each scenario at most {config.limits.max_scenario_seconds}s; bursts at most "
        f"{config.limits.max_burst_requests} requests x {config.limits.max_concurrency} concurrent")
    if docker:
        leftovers = _docker("ps", "-a", "-q", "--filter", f"label={LABEL}.project={_safe(project.name)}", timeout=30).stdout.split()
        add("no other experiment is running on this project", not leftovers,
            "ok" if not leftovers else f"{len(leftovers)} container(s) from another experiment still exist")
    return checks


def _safe(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", text)[:60]


class Sandbox:
    def __init__(self, project: Path, config: AssessmentConfig, label: str = "env"):
        self.project = Path(project).resolve()
        self.config = config
        self.id = f"{uuid.uuid4().hex[:10]}_{_safe(label)}"
        self.network = f"aiforge_chaos_{self.id}"
        self.app = f"aiforge_chaos_app_{self.id}"
        self.probe_c = f"aiforge_chaos_probe_{self.id}"
        self.deps: Dict[str, str] = {d.name: f"aiforge_chaos_dep_{d.name}_{self.id}" for d in config.dependencies}
        self.volume: Optional[str] = None
        self.labels = ["--label", f"{LABEL}={self.id}", "--label", f"{LABEL}.project={_safe(self.project.name)}"]
        self.app_url = "http://app:8000"
        self.started_at: Optional[float] = None

    # --- lifecycle -------------------------------------------------------------------------------

    def setup(self) -> List[str]:
        """Create the network, install dependencies, start stubs, the app and the probe. Returns the steps done."""
        from backend.execution.docker_test_sandbox import IMAGE
        from backend.execution.preview_manager import backend_commands, backend_entry
        steps = []
        created = _docker("network", "create", "--internal", *self.labels, self.network, timeout=60)
        if created.returncode != 0:
            raise SandboxError("could not create an isolated (internal) network: " + (created.stderr or "")[-300:])
        steps.append(f"created internal network {self.network} (no external route)")
        entry = backend_entry(self.project)
        cmds = backend_commands(self.project, f"chaos_{self.id}", entry, TTL_SECONDS)
        self.volume = cmds["volume"]
        inst = _docker(*cmds["install"], timeout=900)
        if inst.returncode != 0:
            raise SandboxError("dependency install failed: " + redact((inst.stdout + inst.stderr)[-1500:]))
        steps.append("installed the app's requirements into a throwaway volume (no project code ran)")
        for spec in self.config.dependencies:
            self._start_dependency(spec, IMAGE)
            steps.append(f"started stub dependency '{spec.name}' (reachable as http://{spec.name}:8080)")
        run = self._app_command(cmds["run"], IMAGE)
        started = _docker(*run, timeout=120)
        if started.returncode != 0:
            raise SandboxError("the app container did not start: " + (started.stderr or "")[-500:])
        self.started_at = time.monotonic()
        steps.append(f"started the app in a hardened container ({self.config.limits.memory_mb} MB, "
                     f"{self.config.limits.cpus} CPU), on the internal network only")
        probe = _docker("run", "-d", "--name", self.probe_c, *self.labels, "--network", self.network,
                        *DEP_LIMITS, IMAGE, "timeout", str(TTL_SECONDS), "sleep", str(TTL_SECONDS), timeout=120)
        if probe.returncode != 0:
            raise SandboxError("the probe container did not start: " + (probe.stderr or "")[-300:])
        steps.append("started the probe container on the same network")
        return steps

    def _start_dependency(self, spec: DependencySpec, image: str) -> None:
        res = _docker("run", "-d", "--name", self.deps[spec.name], *self.labels, "--network", self.network,
                      "--network-alias", spec.name, *DEP_LIMITS, "-e", f"STUB_ROUTES={json.dumps(spec.routes)}",
                      image, "timeout", str(TTL_SECONDS), "python", "-c", STUB_DEPENDENCY, timeout=120)
        if res.returncode != 0:
            raise SandboxError(f"stub dependency '{spec.name}' did not start: " + (res.stderr or "")[-300:])

    def _app_command(self, run: List[str], image: str) -> List[str]:
        """The preview's hardened run command, moved onto the internal network with this run's limits."""
        out, skip = [], False
        for i, arg in enumerate(run):
            if skip:
                skip = False
                continue
            if arg == "-p":                                    # nothing is published on the host
                skip = True
                continue
            if arg == "--name":
                out += ["--name", self.app]
                skip = True
                continue
            if i > 0 and run[i - 1] == "--memory":
                arg = f"{self.config.limits.memory_mb}m"
            if i > 0 and run[i - 1] == "--cpus":
                arg = str(self.config.limits.cpus)
            if arg == image:
                envs = [x for d in self.config.dependencies for x in ("-e", f"{d.env_var}=http://{d.name}:8080")]
                out += [*self.labels, "--network", self.network, "--network-alias", "app", *envs]
            out.append(arg)
        return out

    def cleanup(self) -> List[str]:
        """Remove every container, the network and the volume of this experiment (also after errors)."""
        done = []
        ids = _docker("ps", "-a", "-q", "--filter", f"label={LABEL}={self.id}", timeout=30).stdout.split()
        if ids:
            _docker("rm", "-f", *ids, timeout=120)
            done.append(f"removed {len(ids)} container(s)")
        if _docker("network", "rm", self.network, timeout=60).returncode == 0:
            done.append("removed the internal network")
        if self.volume and _docker("volume", "rm", "-f", self.volume, timeout=60).returncode == 0:
            done.append("removed the dependency volume")
        return done

    # --- observation ---------------------------------------------------------------------------------

    def probe(self, endpoints: List[Target], count: int = 1, concurrency: int = 1, timeout: float = 10.0) -> List[Dict[str, Any]]:
        eps = json.dumps([[t.method, t.path] for t in endpoints])
        wall = max(30.0, count * len(endpoints) * (timeout + 1) / max(1, concurrency) + 20)
        res = _docker("exec", self.probe_c, "python", "-c", PROBE, self.app_url, eps, str(count), str(concurrency),
                      str(timeout), timeout=wall)
        if res.returncode != 0:
            raise SandboxError("probe failed: " + (res.stderr or res.stdout)[-300:])
        return json.loads(res.stdout.strip().splitlines()[-1])["results"]

    def openapi_endpoints(self, limit: int = 6) -> List[Target]:
        res = _docker("exec", self.probe_c, "python", "-c",
                      "import urllib.request,sys;print(urllib.request.urlopen(sys.argv[1]+'/openapi.json',timeout=5).read().decode())",
                      self.app_url, timeout=30)
        try:
            spec = json.loads(res.stdout)
        except ValueError:
            return []
        out = []
        for path, ops in sorted((spec.get("paths") or {}).items()):
            op = (ops or {}).get("get")
            if op and "{" not in path and not any(p.get("required") for p in op.get("parameters") or []):
                out.append(Target(method="GET", path=path))
        return out[:limit]

    def wait_healthy(self, health: Target, budget_s: float) -> Optional[float]:
        """Seconds until the health endpoint answers < 400, or None within the budget."""
        start = time.monotonic()
        while time.monotonic() - start < budget_s:
            try:
                r = self.probe([health], 1, 1, 3.0)[0]
                if r.get("status") is not None and r["status"] < 400:
                    return round(time.monotonic() - start, 2)
            except SandboxError:
                pass
            time.sleep(0.5)
        return None

    def control(self, dependency: str, mode: str, delay_ms: int = 0) -> str:
        res = _docker("exec", self.probe_c, "python", "-c", CONTROL, f"http://{dependency}:8080",
                      json.dumps({"mode": mode, "delay_ms": delay_ms}), timeout=30)
        if res.returncode != 0:
            raise SandboxError(f"could not switch '{dependency}' to {mode}: " + (res.stderr or "")[-200:])
        return res.stdout.strip()

    def stop_dependency(self, dependency: str) -> None:
        if dependency not in self.deps:
            raise SandboxError("only this experiment's own dependencies can be stopped")
        _docker("stop", "-t", "1", self.deps[dependency], timeout=60)

    def start_dependency(self, dependency: str) -> None:
        if dependency not in self.deps:
            raise SandboxError("only this experiment's own dependencies can be started")
        _docker("start", self.deps[dependency], timeout=60)

    def restart_app(self) -> None:
        _docker("restart", "-t", "2", self.app, timeout=120)

    def app_state(self) -> Dict[str, Any]:
        res = _docker("inspect", "-f", "{{json .State}}", self.app, timeout=30)
        try:
            s = json.loads(res.stdout)
        except ValueError:
            return {}
        return {"running": s.get("Running"), "oom_killed": s.get("OOMKilled"), "exit_code": s.get("ExitCode"),
                "restarting": s.get("Restarting")}

    def app_stats(self) -> Tuple[Optional[float], Optional[float]]:
        from backend.performance.engineer.runner import parse_docker_stats
        res = _docker("stats", "--no-stream", "--format", "{{json .}}", self.app, timeout=30)
        line = (res.stdout or "").strip().splitlines()
        parsed = parse_docker_stats(line[0]) if line else None
        return parsed if parsed else (None, None)

    def app_logs(self, tail: int = 80) -> str:
        res = _docker("logs", "--tail", str(tail), self.app, timeout=30)
        return redact((res.stdout + res.stderr)[-6000:])
