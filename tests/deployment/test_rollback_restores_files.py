from backend.deployment.rollback_manager import RollbackManager


def test_rollback_restores_the_checkpointed_files(tmp_path):
    project = tmp_path / "todo_app"
    (project / "backend").mkdir(parents=True)
    (project / "backend" / "main.py").write_text("VERSION = 1\n", encoding="utf-8")

    manager = RollbackManager()
    tag = manager.create_deployment_checkpoint(project)

    # A failed deploy changes and adds files...
    (project / "backend" / "main.py").write_text("VERSION = 2  # broken\n", encoding="utf-8")
    (project / "backend" / "new_bug.py").write_text("raise SystemExit\n", encoding="utf-8")

    entry = manager.trigger_rollback(reason="health check failed", project_path=project)

    assert entry["status"] == "RESTORED" and entry["restored_version"] == tag
    assert (project / "backend" / "main.py").read_text(encoding="utf-8") == "VERSION = 1\n"
    assert not (project / "backend" / "new_bug.py").exists()


def test_rollback_without_a_checkpoint_does_not_claim_success(tmp_path):
    project = tmp_path / "no_checkpoints"
    project.mkdir()
    entry = RollbackManager().trigger_rollback(reason="smoke tests failed", project_path=project)
    assert entry["status"] == "NO_CHECKPOINT" and entry["restored_version"] is None
