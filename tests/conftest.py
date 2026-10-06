import pytest


@pytest.fixture(autouse=True)
def _isolated_generation_store(tmp_path, monkeypatch):
    """
    Point the app-wide generation store at a temp file for every test, so API tests that
    create, cancel or list generations never write into backend/data/generations.json.
    """
    from backend.generation.store import global_generation_store

    path = tmp_path / "generations.json"
    path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(global_generation_store, "_path", path)
