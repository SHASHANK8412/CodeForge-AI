"""
Regression: a project's tests run with an empty pytest config that once lived directly in the shared temp folder.
pytest's collection tree starts at the config's directory, so it walked every other process's temporary
workspace there; one deleted mid-scan failed the collection (FileNotFoundError), and Autopilot then rejected a
harmless change as "tests passed before the change and fail after it". The config now has its own directory and
conftest discovery stops at the project.
"""

import subprocess
from pathlib import Path

from backend.execution.project_runner import ProjectRunner


def test_project_tests_never_scan_or_load_anything_outside_the_project(tmp_path, monkeypatch):
    import tempfile
    shared_tmp = tmp_path / "shared_temp"                       # stands in for the system temp folder
    shared_tmp.mkdir()
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(shared_tmp))
    project = shared_tmp / "aiforge_autopilot_check_x" / "shop"
    (project / "tests").mkdir(parents=True)
    (project / "tests" / "test_ok.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    (shared_tmp / "other_workspace").mkdir()                    # another process's workspace next to it
    (shared_tmp / "conftest.py").write_text("raise RuntimeError('a conftest outside the project was loaded')\n", encoding="utf-8")
    cmd = ProjectRunner._isolated_pytest_command(project)
    ini = Path(cmd[cmd.index("-c") + 1])
    assert ini.parent != shared_tmp and ini.parent.name == "aiforge_isolated_pytest" and list(ini.parent.iterdir()) == [ini]
    assert cmd[cmd.index("--confcutdir") + 1] == str(project)
    debug = tmp_path / "debug.log"
    res = subprocess.run(cmd + ["--collect-only", "-q", f"--debug={debug}"], cwd=project, capture_output=True, text=True, timeout=120)
    assert res.returncode == 0, res.stdout + res.stderr          # the outside conftest.py was not imported
    trace = debug.read_text(encoding="utf-8", errors="replace")
    assert "other_workspace" not in trace and "aiforge_autopilot_check_x>" not in trace
    run = subprocess.run(cmd, cwd=project, capture_output=True, text=True, timeout=120)
    assert run.returncode == 0 and "1 passed" in run.stdout
