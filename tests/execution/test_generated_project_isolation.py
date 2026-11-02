"""A generated project's tests must import the generated code, not AIForge's own packages."""
from backend.execution.project_runner import ProjectRunner


def test_generated_backend_package_wins_over_the_platform_backend(tmp_path):
    project = tmp_path / "todo_app"
    (project / "backend").mkdir(parents=True)
    (project / "tests").mkdir()
    # Same import path as AIForge's own backend/routes package, which has no `app`.
    (project / "backend" / "routes.py").write_text("app = 'generated'\n", encoding="utf-8")
    (project / "tests" / "test_api.py").write_text(
        "from backend.routes import app\n\n"
        "def test_uses_generated_code():\n"
        "    assert app == 'generated'\n",
        encoding="utf-8",
    )

    result = ProjectRunner().run_project(str(project))

    assert result.exit_code == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout
    assert (project / "backend" / "__init__.py").exists()
