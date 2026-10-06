import pytest


@pytest.fixture(autouse=True)
def _isolated_generation_store(tmp_path_factory, monkeypatch):
    """
    Point the app-wide generation store at a temp file for every test, so API tests that
    create, cancel or list generations never write into backend/data/generations.json.
    """
    from backend.generation.store import global_generation_store

    # Its own folder: tests that scan their tmp_path for *.json must not see this file.
    path = tmp_path_factory.mktemp("generation_store") / "generations.json"
    path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(global_generation_store, "_path", path)


@pytest.fixture(autouse=True)
def _local_test_sandbox(monkeypatch):
    """Generated-project tests run locally unless a test opts into the Docker sandbox."""
    monkeypatch.setenv("AIFORGE_TEST_SANDBOX", "local")
