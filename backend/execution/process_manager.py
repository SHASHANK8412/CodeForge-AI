import os
import subprocess
import logging
import threading
from collections import deque
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

logger = logging.getLogger("aiforge.execution.process_manager")


class ProcessManager:
    """
    ProcessManager spawns, tracks, and terminates background execution processes safely.
    """

    def __init__(self):
        self.active_processes: Dict[str, subprocess.Popen] = {}
        self._logs: Dict[str, Dict[str, deque]] = {}
        self._meta: Dict[str, tuple] = {}

    def run_command(self, cmd: str, cwd: str = ".", timeout_seconds: int = 15) -> Dict[str, Any]:
        """Runs a command synchronously with timeout handling."""
        try:
            res = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds
            )
            return {
                "exit_code": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "command": cmd
            }
        except subprocess.TimeoutExpired:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout_seconds} seconds.",
                "command": cmd
            }
        except Exception as e:
            return {
                "exit_code": 1,
                "stdout": "",
                "stderr": str(e),
                "command": cmd
            }


    # --- Background services (live preview / local deploy) -------------------------------

    def _key(self, project_id: str, service_name: str) -> str:
        return f"{project_id}:{service_name}"

    def start_process(self, project_id: str, service_name: str, command: str, cwd: str = ".",
                      port: Optional[int] = None, env_vars: Optional[Dict[str, str]] = None) -> "ProcessInfo":
        """Launch a long-running service in the background and capture its output."""
        self.stop_process(project_id, service_name)
        proc = subprocess.Popen(
            command, shell=True, cwd=cwd, env={**os.environ, "PYTHONUNBUFFERED": "1", **(env_vars or {})},
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace",
        )
        key = self._key(project_id, service_name)
        self.active_processes[key] = proc
        self._logs[key] = {"stdout": deque(maxlen=500), "stderr": deque(maxlen=500)}
        for stream_name in ("stdout", "stderr"):
            threading.Thread(target=self._pump, args=(getattr(proc, stream_name), self._logs[key][stream_name]),
                             daemon=True).start()
        self._meta[key] = (command, port)
        logger.info("Started %s for %s (pid=%s): %s", service_name, project_id, proc.pid, command)
        return ProcessInfo(project_id=project_id, service_name=service_name, pid=proc.pid,
                           port=port, command=command, status="STARTING")

    @staticmethod
    def _pump(stream, sink) -> None:
        for line in iter(stream.readline, ""):
            sink.append(line.rstrip("\n"))
        stream.close()

    def get_status(self, project_id: str, service_name: str) -> Optional["ProcessInfo"]:
        key = self._key(project_id, service_name)
        proc = self.active_processes.get(key)
        if proc is None:
            return None
        command, port = self._meta.get(key, ("", None))
        code = proc.poll()
        return ProcessInfo(project_id=project_id, service_name=service_name, pid=proc.pid, port=port,
                           command=command, status="RUNNING" if code is None else f"EXITED({code})")

    def get_logs(self, project_id: str, service_name: str) -> Dict[str, List[str]]:
        logs = self._logs.get(self._key(project_id, service_name), {})
        return {"stdout": list(logs.get("stdout", [])), "stderr": list(logs.get("stderr", []))}

    def stop_process(self, project_id: str, service_name: str) -> bool:
        proc = self.active_processes.pop(self._key(project_id, service_name), None)
        if proc is None:
            return False
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        return True


class ProcessInfo(BaseModel):
    project_id: str
    service_name: str
    pid: int
    port: Optional[int] = None
    command: str
    status: str


# Global ProcessManager Instance
global_process_manager = ProcessManager()
