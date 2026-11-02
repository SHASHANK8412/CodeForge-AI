"""Generated projects get their own environment; their requirements never touch AIForge's."""
import sys

from backend.execution.project_env import ENV_DIRNAME, ensure_project_env, env_python, site_packages
from backend.execution.project_runner import ProjectRunner


def _project(tmp_path, requirements: str):
    project = tmp_path / "app"
    (project / "backend").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / "requirements.txt").write_text(requirements, encoding="utf-8")
    return project


def test_requirements_install_into_the_project_venv(tmp_path):
    project = _project(tmp_path, "")  # empty file: no network needed
    res = ensure_project_env(project)
    assert res["ok"] and env_python(project).exists() and site_packages(project) is not None
    assert str(env_python(project)) != sys.executable
    assert ensure_project_env(project)["cached"] is True


def test_generated_tests_can_import_the_projects_own_dependencies(tmp_path):
    project = _project(tmp_path, "")
    ensure_project_env(project)
    # Stand-in for a package from the project's requirements that AIForge itself doesn't have.
    (site_packages(project) / "only_in_project_env.py").write_text("VALUE = 7\n", encoding="utf-8")
    (project / "tests" / "test_dep.py").write_text(
        "from only_in_project_env import VALUE\n\ndef test_value():\n    assert VALUE == 7\n", encoding="utf-8")

    result = ProjectRunner().run_project(str(project))
    assert result.exit_code == 0, result.stdout + result.stderr
