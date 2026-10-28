import pytest


@pytest.fixture(autouse=True)
def _local_dev_auth(monkeypatch):
    """The API requires authentication by default; these suites call it in-process without a token, in the explicit
    single-user development mode (see tests/conftest.py)."""
    monkeypatch.setenv("AIFORGE_AUTH_MODE", "local-dev")
    monkeypatch.delenv("AIFORGE_ENV", raising=False)
