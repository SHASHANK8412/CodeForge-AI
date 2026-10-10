"""The JWT signing key must never be a value from the source code."""
import importlib

import backend.auth.security as security


def test_signing_key_is_not_the_old_hardcoded_value():
    assert security.SECRET_KEY != "aiforge_jwt_super_secret_production_key_2026"
    assert len(security.SECRET_KEY) >= 32


def test_jwt_secret_env_wins(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "x" * 40)
    assert security._load_secret_key() == "x" * 40


def test_generated_key_is_persisted(monkeypatch, tmp_path):
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.setattr(security, "_SECRET_FILE", tmp_path / "jwt_secret.key")
    first = security._load_secret_key()
    assert (tmp_path / "jwt_secret.key").read_text(encoding="utf-8") == first
    assert security._load_secret_key() == first, "must stay stable across restarts"


def test_tokens_round_trip():
    importlib.reload(security)
    token = security.create_access_token({"sub": "user_1"})
    assert security.decode_access_token(token)["sub"] == "user_1"


def test_require_auth_rejects_anonymous_requests(monkeypatch):
    from fastapi.testclient import TestClient
    from backend.main import app
    client = TestClient(app)
    assert client.get("/api/auth/me").status_code == 200  # local single-user default
    monkeypatch.setenv("AIFORGE_REQUIRE_AUTH", "1")
    assert client.get("/api/auth/me").status_code == 401
