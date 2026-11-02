import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import backend.routes.export as export
from backend.github.github_api_service import GitHubAuthError
from backend.github.publisher import global_github_publisher

FILES = {"README.md": "# demo\n", "app.py": "print('hi')\n"}


@pytest.fixture(autouse=True)
def _no_github_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)


def test_publisher_without_token_refuses_instead_of_simulating():
    with pytest.raises(GitHubAuthError):
        global_github_publisher.publish_project(project_id="demo", files_manifest=FILES)


def test_export_github_route_without_token_is_401_not_a_fake_repo_url():
    app = FastAPI()
    app.include_router(export.router)
    res = TestClient(app).post("/api/export/github", json={"project_id": "demo", "files": FILES})
    assert res.status_code == 401
    assert "github.com" not in res.text


def test_publisher_refuses_to_write_outside_the_project_directory(tmp_path):
    hostile = {"../escaped.txt": "nope"}
    with pytest.raises(ValueError):
        global_github_publisher.publish_project(
            project_id="demo", files_manifest=hostile, token="test-token-not-real", working_dir=tmp_path / "proj"
        )
    assert not (tmp_path / "escaped.txt").exists()
