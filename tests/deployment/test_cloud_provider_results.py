import asyncio

import pytest

from backend.deployment.providers.neon_provider import global_neon_provider
from backend.deployment.providers.render_provider import global_render_provider
from backend.deployment.providers.vercel_provider import global_vercel_provider

PROVIDERS = [
    (global_vercel_provider, "VERCEL_TOKEN"),
    (global_render_provider, "RENDER_API_KEY"),
    (global_neon_provider, "NEON_API_KEY"),
]


@pytest.mark.parametrize("provider,token_env", PROVIDERS)
def test_missing_credentials_reports_not_configured(provider, token_env, monkeypatch):
    monkeypatch.delenv(token_env, raising=False)
    result = asyncio.run(provider.deploy("demo-project", {}))
    assert result["status"] == "NOT_CONFIGURED"
    assert result["url"] is None
    assert token_env in result["message"]


@pytest.mark.parametrize("provider,token_env", PROVIDERS)
def test_credentials_present_never_fakes_a_live_deploy(provider, token_env, monkeypatch):
    monkeypatch.setenv(token_env, "test-token-not-real")
    result = asyncio.run(provider.deploy("demo-project", {}))
    assert result["status"] == "MANUAL_DEPLOY_REQUIRED"
    assert result["url"] is None
    assert "test-token-not-real" not in str(result)
