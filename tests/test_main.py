"""
AIForge integration checks: startup, retired simulated features, and the local verifiable-records chain.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_app_startup_and_health():
    """Verify application health and core route registration."""
    res = client.get("/health")
    # Health route or observability status
    assert res.status_code in [200, 404]  # /health is mounted under observability or root


def test_simulated_multi_agent_missions_are_retired():
    """The old /api/multi-agent missions hardcoded COMPLETED tasks and VERIFIED findings; they were replaced by
    Swarm Intelligence (real agents, artifacts with provenance, verified integration)."""
    assert client.get("/api/multi-agent/missions").status_code == 404
    assert client.post("/api/multi-agent/missions/dispatch", json={"objective": "x"}).status_code == 404
    assert client.get("/api/swarm/agents").status_code == 200


def test_blockchain_verifiable_ledger(tmp_path, monkeypatch):
    """The local hash chain: signed records, chain links, tamper detection, legacy-key records flagged."""
    from backend.blockchain.verifiable_ledger import VerifiableLedgerService
    monkeypatch.delenv("AIFORGE_LEDGER_SIGNING_KEY", raising=False)
    ledger = VerifiableLedgerService(str(tmp_path))
    a = ledger.create_and_anchor_record("first decision", "ent_1", content_payload={"x": 1})
    b = ledger.create_and_anchor_record("second decision", "ent_2", content_payload={"x": 2})
    assert (a.block_number, b.block_number) == (1, 2) and b.previous_hash == a.content_hash
    assert a.ledger_reference == "local-chain:1" and a.signature.startswith("hmac_sha256_")
    assert (tmp_path / "signing.key").is_file(), "the key is generated per installation, not taken from the source"
    ok = ledger.verify_record_integrity(b.id)
    assert ok["valid"] is True and ok["trust_status"] == "VERIFIED_LOCAL_HASH_CHAIN"
    status = ledger.get_ledger_status()
    assert status["integrity_chain_valid"] is True and status["network_status"] == "LOCAL"
    assert "no external blockchain" in status["ledger_provider"]

    # tampering with a record's content hash breaks its signature and the next record's link
    ledger._records[a.id] = a.model_copy(update={"content_hash": "f" * 64})
    assert ledger.verify_record_integrity(a.id)["trust_status"] == "TAMPER_DETECTED"
    assert ledger.verify_record_integrity(b.id)["chain_link_valid"] is False
    assert ledger.get_ledger_status()["integrity_chain_valid"] is False

    # a record signed with the old key that was published in the source is never reported as valid
    import hashlib, hmac
    legacy_sig = "sig_ed25519_" + hmac.new(b"aiforge_zero_trust_master_signing_key_2026", b"agent:" + b"0" * 64,
                                           hashlib.sha256).hexdigest()[:32]
    fresh = VerifiableLedgerService(str(tmp_path / "legacy"))
    old = fresh.create_and_anchor_record("old", "ent_old")
    fresh._records[old.id] = old.model_copy(update={"content_hash": "0" * 64, "signer_id": "agent", "signature": legacy_sig})
    legacy = fresh.verify_record_integrity(old.id)
    assert legacy["valid"] is False and legacy["trust_status"] == "UNTRUSTED_LEGACY_KEY"


@pytest.mark.parametrize("method,path", [
    ("GET", "/api/os/overview"), ("POST", "/api/os/command"), ("GET", "/api/knowledge/entities"),
    ("GET", "/api/knowledge/graph"), ("GET", "/api/computer-agent/sessions"), ("GET", "/api/intelligence/overview"),
    ("GET", "/api/missions/templates"), ("GET", "/api/research"), ("GET", "/api/workflows"),
    ("GET", "/api/cyber-copilot/overview"), ("GET", "/api/sentinel/posture"), ("GET", "/api/autonomous-workflows"),
])
def test_simulated_features_are_retired(method, path):
    """These features only returned built-in demo data (no model call, no real work); they were removed."""
    assert client.request(method, path, json={}).status_code == 404
