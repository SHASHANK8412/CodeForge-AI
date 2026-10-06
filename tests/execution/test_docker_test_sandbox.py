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
