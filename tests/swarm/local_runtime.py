"""
A test-only runtime for the fast Swarm tests: the sample backend (fixed code from tests/swarm/sample.py, never
model output) runs under uvicorn on 127.0.0.1 and the real harness.mjs runs under the host's node. Everything
else - the plan, the harness, evaluation, classification, repair - is the production code. It reports itself as
NOT isolated, so an engine that requires isolation never treats its results as a successful mission; the
genuine test in test_swarm_v2.py uses the Docker runtime.
"""

import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict

from backend.swarm import runtime as rt


class LocalRuntime:
    environment = "local test runtime (host uvicorn + host node; not isolated)"

    def __init__(self, tamper=None):
        self.proc = None
        self.work = None
        self.tamper = tamper              # optional fn(raw, call_no) -> raw, to simulate flaky behaviour
        self.calls = 0
        self.stopped = False

    def start(self, workspace: Path, files: Dict[str, str]) -> Dict[str, Any]:
        from backend.execution.preview_manager import backend_entry
        entry = backend_entry(workspace)
        if entry is None:
            raise rt.AppFailed("the integrated backend is not runnable")
        self.files = files
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            self.port = s.getsockname()[1]
        cwd = workspace if entry["workdir"] == "." else workspace / entry["workdir"]
        env = {k: v for k, v in os.environ.items() if k in ("PATH", "SYSTEMROOT", "TEMP", "TMP")}
        env["PYTHONPATH"] = str(cwd)
        self.proc = subprocess.Popen([sys.executable, "-m", "uvicorn", entry["module"], "--host", "127.0.0.1", "--port", str(self.port)],
                                     cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                raise rt.AppFailed("the backend exited", self.proc.stdout.read().decode(errors="replace"))
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{self.port}/openapi.json", timeout=2)
                return {"steps": ["started the sample backend locally (test runtime)"]}
            except OSError:
                time.sleep(0.2)
        raise rt.AppFailed("the backend did not answer in 30s")

    def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        self.calls += 1
        if self.work:
            shutil.rmtree(self.work, ignore_errors=True)
        self.work = rt.prepare_workdir(self.files, {**plan, "root": "", "egress": []})
        local_plan = {**plan, "base": f"http://127.0.0.1:{self.port}", "root": self.work.as_posix(), "egress": []}
        (self.work / "plan.json").write_text(__import__("json").dumps(local_plan), encoding="utf-8")
        res = subprocess.run(["node", str(self.work / "harness.mjs"), str(self.work / "plan.json")], capture_output=True,
                             text=True, timeout=60)
        raw = rt.parse_output(res.stdout)
        return self.tamper(raw, self.calls) if self.tamper else raw

    def isolation(self) -> Dict[str, Any]:
        return {"verified": False, "checks": [{"check": "isolated environment", "passed": False,
                                               "observed": "test-only host runtime"}]}

    def stop(self) -> Dict[str, Any]:
        self.stopped = True
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        if self.work:
            shutil.rmtree(self.work, ignore_errors=True)
        return {"done": ["stopped the local backend"], "verified": True}
