"""Generated tests run in a Docker container when Docker is available."""
import pytest

from backend.execution import docker_test_sandbox as sandbox
from backend.execution.project_runner import ProjectRunner


def _project(tmp_path, test_body: str):
    project = tmp_path / "app"
    (project / "backend").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / "backend" / "logic.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (project / "requirements.txt").write_text("", encoding="utf-8")
    (project / "tests" / "test_logic.py").write_text(test_body, encoding="utf-8")
    return project


def test_mode_switch(monkeypatch):
    monkeypatch.setenv("AIFORGE_TEST_SANDBOX", "local")
    assert sandbox.should_use_docker() is False
    monkeypatch.setenv("AIFORGE_TEST_SANDBOX", "docker")
    assert sandbox.should_use_docker() is True


@pytest.mark.skipif(not sandbox.docker_available(), reason="Docker daemon not reachable")
def test_tests_run_inside_a_linux_container(tmp_path, monkeypatch):
    monkeypatch.setenv("AIFORGE_TEST_SANDBOX", "docker")
    project = _project(tmp_path,
        "import sys\nfrom backend.logic import add\n\n"
        "def test_runs_in_container():\n    assert sys.platform == 'linux'\n\n"
        "def test_add():\n    assert add(2, 3) == 5\n")
    result = ProjectRunner().run_project(str(project))
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "2 passed" in result.stdout


@pytest.mark.skipif(not sandbox.docker_available(), reason="Docker daemon not reachable")
def test_failing_tests_are_reported_as_failures(tmp_path, monkeypatch):
    monkeypatch.setenv("AIFORGE_TEST_SANDBOX", "docker")
    project = _project(tmp_path, "def test_broken():\n    assert 1 == 2\n")
    result = ProjectRunner().run_project(str(project))
    assert result.exit_code != 0 and "1 failed" in result.stdout


@pytest.mark.skipif(not sandbox.docker_available(), reason="Docker daemon not reachable")
def test_tests_run_without_network_or_root_and_are_cleaned_up(tmp_path, monkeypatch):
    import subprocess
    monkeypatch.setenv("AIFORGE_TEST_SANDBOX", "docker")
    project = _project(tmp_path,
        "import os, socket\n\n"
        "def test_not_root():\n    assert os.getuid() != 0\n\n"
        "def test_no_network():\n"
        "    try:\n        socket.create_connection(('1.1.1.1', 53), timeout=3)\n        reached = True\n"
        "    except OSError:\n        reached = False\n"
        "    assert reached is False\n")
    result = ProjectRunner().run_project(str(project))
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "2 passed" in result.stdout

    exe = sandbox.docker_exe()
    leftovers = subprocess.run([exe, "ps", "-a", "--filter", "name=aiforge_test_", "-q"], capture_output=True, text=True).stdout.strip()
    volumes = subprocess.run([exe, "volume", "ls", "--filter", "name=aiforge_deps_", "-q"], capture_output=True, text=True).stdout.strip()
    assert leftovers == "" and volumes == ""


@pytest.mark.skipif(not sandbox.docker_available(), reason="Docker daemon not reachable")
def test_runaway_tests_are_stopped(tmp_path):
    project = _project(tmp_path, "def test_forever():\n    while True:\n        pass\n")
    result = sandbox.run_pytest_in_docker(project, timeout_seconds=60)
    assert result.timed_out is True
