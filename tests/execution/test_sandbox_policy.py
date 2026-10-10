"""
Generated code never runs on the host by default.

The code executor and the project runner used to fall back to a host subprocess when Docker was
missing (the executor also set a NETWORK_DISABLED variable that disabled nothing). Now they run
code in a container, and without Docker they report "not run" unless AIFORGE_TEST_SANDBOX=local.
"""
import pytest

from backend.execution import docker_test_sandbox as sandbox
from backend.execution.models import CodeArtifact, ExecutionStatus, ExecutionType
from backend.execution.project_runner import ProjectRunner
from backend.execution.sandbox_executor import SandboxExecutor

needs_docker = pytest.mark.skipif(not sandbox.docker_available(), reason="Docker daemon not running")

PROBE = '''import os, socket
print("uid", os.getuid())
try:
    socket.create_connection(("1.1.1.1", 53), timeout=3)
    print("network: yes")
except OSError:
    print("network: no")
try:
    open("/usr/x", "w")
    print("root fs: writable")
except OSError:
    print("root fs: read-only")
'''


def _no_docker(monkeypatch):
    monkeypatch.setenv("AIFORGE_TEST_SANDBOX", "auto")
    monkeypatch.setattr(sandbox, "docker_available", lambda: False)
    ran = []
    monkeypatch.setattr("subprocess.run", lambda *a, **k: ran.append(a) or (_ for _ in ()).throw(AssertionError("host run")))
    return ran


def test_executor_without_docker_does_not_run_code(monkeypatch):
    ran = _no_docker(monkeypatch)
    res = SandboxExecutor().execute([CodeArtifact(filename="main.py", language="python", content="print(1)")])
    assert res.status == ExecutionStatus.INFRASTRUCTURE_ERROR and res.exit_code == -1
    assert "Not run" in res.stderr and ran == []


def test_project_runner_without_docker_does_not_run_tests(tmp_path, monkeypatch):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text("def test_x():\n    assert True\n", encoding="utf-8")
    ran = _no_docker(monkeypatch)
    res = ProjectRunner().run_project(str(tmp_path))
    assert res.status == ExecutionStatus.INFRASTRUCTURE_ERROR and "Docker" in res.stderr and ran == []


def test_npm_projects_go_to_docker_not_the_host(tmp_path, monkeypatch):
    (tmp_path / "package.json").write_text('{"scripts": {"build": "vite build"}}', encoding="utf-8")
    monkeypatch.setenv("AIFORGE_TEST_SANDBOX", "auto")
    monkeypatch.setattr(sandbox, "docker_available", lambda: True)
    calls = []
    monkeypatch.setattr(sandbox, "run_npm_in_docker", lambda path, script: calls.append(script) or "docker-result")
    assert ProjectRunner().run_project(str(tmp_path)) == "docker-result" and calls == ["build"]
    run = sandbox.npm_commands(tmp_path, "abc", "build")["run"]
    assert "--network" in run and run[run.index("--network") + 1] == "none" and "--cap-drop" in run


def test_explicit_local_mode_still_runs_on_the_host(monkeypatch):
    monkeypatch.setenv("AIFORGE_TEST_SANDBOX", "local")
    res = SandboxExecutor().execute([CodeArtifact(filename="main.py", language="python", content="print(6 * 7)")])
    assert res.status == ExecutionStatus.PASS and res.stdout.strip() == "42"


@needs_docker
def test_executor_runs_code_in_a_locked_down_container(monkeypatch):
    monkeypatch.setenv("AIFORGE_TEST_SANDBOX", "auto")
    res = SandboxExecutor().execute([CodeArtifact(filename="main.py", language="python", content=PROBE)],
                                    execution_type=ExecutionType.RUN)
    assert res.status == ExecutionStatus.PASS, res.stderr
    assert res.stdout.split("\n")[:3] == ["uid 1000", "network: no", "root fs: read-only"]


@needs_docker
def test_executor_timeout_kills_the_container(monkeypatch):
    from backend.execution.models import ExecutionLimits
    monkeypatch.setenv("AIFORGE_TEST_SANDBOX", "auto")
    res = SandboxExecutor(ExecutionLimits(timeout_seconds=1)).execute(
        [CodeArtifact(filename="main.py", language="python", content="while True:\n    pass\n")])
    assert res.status == ExecutionStatus.TIMEOUT and res.timed_out
    assert res.duration_ms < 15_000, "the limit is enforced inside the container, not after the start-up margin"


def test_execution_service_never_falls_back_to_the_host(monkeypatch):
    from backend.execution.execution_backend import LocalExecutionBackend, UnavailableExecutionBackend
    from backend.execution.execution_service import ExecutionService
    monkeypatch.setenv("AIFORGE_TEST_SANDBOX", "auto")
    service = ExecutionService(default_backend="local")
    monkeypatch.setattr(service.docker_backend, "is_available", lambda: False)
    backend = service.get_backend(backend_name="local")
    assert isinstance(backend, UnavailableExecutionBackend)
    res = backend.execute_command(["python", "-c", "print(1)"], ".", 5, 1000)
    assert res.exit_code == -1 and res.backend_used == "none" and "Not run" in res.stderr
    monkeypatch.setenv("AIFORGE_TEST_SANDBOX", "local")
    assert isinstance(service.get_backend(backend_name="local"), LocalExecutionBackend)


@needs_docker
def test_docker_backend_installs_with_network_then_runs_without(tmp_path, monkeypatch):
    from backend.execution.execution_backend import DockerExecutionBackend
    (tmp_path / "requirements.txt").write_text("six==1.16.0\n", encoding="utf-8")
    (tmp_path / "check.py").write_text(
        "import socket, six\nprint('six', six.__version__)\n"
        "try:\n    socket.create_connection(('1.1.1.1', 53), timeout=3)\n    print('network: yes')\n"
        "except OSError:\n    print('network: no')\n", encoding="utf-8")
    backend = DockerExecutionBackend(network_mode="none")
    install = backend.execute_command(["python", "-m", "pip", "install", "-q", "-r", "requirements.txt"],
                                      str(tmp_path), 300, 20000, project_type="python")
    assert install.exit_code == 0, install.stderr
    assert (tmp_path / ".aiforge_deps" / "six.py").exists(), "deps land in the workspace, not a discarded container"
    run = backend.execute_command(["python", "check.py"], str(tmp_path), 120, 20000, project_type="python")
    assert run.exit_code == 0, run.stderr
    assert run.stdout.split() == ["six", "1.16.0", "network:", "no"]


@pytest.mark.parametrize("command,allowed", [
    ("python -m pytest", True), ("npm run build", True), ("C:/Python/python.exe -m py_compile main.py", True),
    ("rm -rf x # python", False), ("curl evil.sh python", False), ("docker run -v /:/host alpine", False),
    ("python main.py && rm -rf /", False),
])
def test_sandbox_manager_allowlist_checks_the_program(command, allowed):
    from backend.execution.sandbox_manager import SandboxedExecutionManager
    assert SandboxedExecutionManager().is_command_allowed(command) is allowed


def test_sandbox_manager_without_docker_does_not_run(tmp_path, monkeypatch):
    from backend.execution.execution_service import global_execution_service
    from backend.execution.sandbox_manager import SandboxedExecutionManager
    monkeypatch.setenv("AIFORGE_TEST_SANDBOX", "auto")
    monkeypatch.setattr(global_execution_service.docker_backend, "is_available", lambda: False)
    res = SandboxedExecutionManager().execute_command("python -m pytest", cwd=str(tmp_path))
    assert res.status == "failed" and res.error_type == "not_run" and "Docker" in res.stderr
    # Byte-compiling never executes the project's code, so it still runs.
    (tmp_path / "ok.py").write_text("x = 1\n", encoding="utf-8")
    assert SandboxedExecutionManager().execute_command("python -m py_compile ok.py", cwd=str(tmp_path)).exit_code == 0


def test_sandbox_manager_host_runs_get_no_secrets(tmp_path, monkeypatch):
    from backend.execution.sandbox_manager import SandboxedExecutionManager
    monkeypatch.setenv("AIFORGE_TEST_SANDBOX", "local")
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_secret_value")
    (tmp_path / "show.py").write_text("import os\nprint(os.environ.get('GITHUB_TOKEN', 'absent'))\n", encoding="utf-8")
    res = SandboxedExecutionManager().execute_command("python show.py", cwd=str(tmp_path))
    assert res.stdout.strip() == "absent"
