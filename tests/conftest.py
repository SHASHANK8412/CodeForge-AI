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


@pytest.fixture(autouse=True)
def _no_llm_repair(monkeypatch):
    """Repair tests exercise the deterministic strategies; the LLM rewrite needs a live model."""
    monkeypatch.setenv("AIFORGE_LLM_REPAIR", "0")


@pytest.fixture(autouse=True)
def _no_container_previews(monkeypatch):
    """Graph tests that reach live_deploy must not start containers; preview tests opt in."""
    monkeypatch.setenv("AIFORGE_PREVIEW", "off")


@pytest.fixture(autouse=True)
def _isolated_time_machine(tmp_path_factory, monkeypatch):
    """Engineering events emitted by any test go to a temp ledger, never backend/data/time_machine."""
    monkeypatch.setenv("AIFORGE_TIME_MACHINE_DIR", str(tmp_path_factory.mktemp("time_machine")))


@pytest.fixture(autouse=True)
def _no_guardian_containers(monkeypatch):
    """The Execution Guardian's container checks (backend startup, frontend build) are BLOCKED - not passed - unless
    a test opts in (the genuine Docker tests do)."""
    monkeypatch.setenv("AIFORGE_GUARDIAN_CONTAINERS", "off")


@pytest.fixture(autouse=True)
def _isolated_execution_guardian(tmp_path_factory, monkeypatch):
    """Verifications recorded by any test (e.g. the workflow's execution_guardian node) go to a temp store, never
    backend/data/execution_guardian."""
    from backend.execution_guardian.service import VerificationStore, global_execution_guardian
    monkeypatch.setattr(global_execution_guardian, "store", VerificationStore(tmp_path_factory.mktemp("execution_guardian")))


@pytest.fixture(autouse=True)
def _isolated_integration_engine(tmp_path_factory, monkeypatch):
    """Contracts and compatibility runs recorded by any test (e.g. the workflow's architect and compatibility nodes) go to
    a temp store, never backend/data/compatibility."""
    from backend.compatibility.service import CompatibilityStore, global_integration_engine
    monkeypatch.setattr(global_integration_engine, "store", CompatibilityStore(tmp_path_factory.mktemp("compatibility")))
