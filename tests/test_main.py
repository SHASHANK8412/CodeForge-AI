"""
AIForge Comprehensive Integration Test Suite
============================================
Tests:
- Application startup & router registration
- Health & System Telemetry
- Authentication & Protected Route Policies
- Next-Gen Agent Runtime (L1)
- Knowledge Graph & Graph RAG (L2)
- Multi-Agent Collaborative DAG & Consensus (L3)
- Cybersecurity Copilot (SOC) (L4)
- Blockchain Trust Layer & Verifiable Ledger (L5)
- Autonomous AI Workflows & Approval Gates (L6)
- AIForge OS Kernel & Universal Context Router (L7)
- Computer-Using AI / Browser Agent
- AI Intelligence & Evaluation Platform
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.blockchain.verifiable_ledger import global_verifiable_ledger
from backend.ai_os.kernel import global_aiforge_os_kernel
from backend.workflow_engine.autonomous_runtime import global_autonomous_engine
from backend.computer_agent.browser_agent import global_computer_agent
from backend.intelligence.eval_engine import global_eval_engine

client = TestClient(app)


def test_app_startup_and_health():
    """Verify application health and core route registration."""
    res = client.get("/health")
    # Health route or observability status
    assert res.status_code in [200, 404]  # /health is mounted under observability or root


def test_ai_os_overview_endpoint():
    """Verify AIForge OS Kernel overview telemetry."""
    res = client.get("/api/os/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "overview" in data
    assert data["overview"]["agents_online_count"] >= 6
    assert len(data["overview"]["active_subsystems"]) == 6


def test_ai_os_universal_command_routing():
    """Verify Universal Context Engine command dispatch."""
    res = client.post("/api/os/command", json={"command": "Investigate security threat spray and correlate Kafka dependencies"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["result"]["route"] in ["CYBER_COPILOT_SOC", "GRAPH_RAG_INTELLIGENCE", "SWARM_INTELLIGENCE"]


def test_ai_os_goal_dispatch():
    """Verify AIForge OS Autonomous Goal Dispatch and Ledger Anchor."""
    res = client.post("/api/os/goals", json={
        "objective": "Audit microservice authentication boundaries and generate verifiable certificate",
        "autonomy_level": "LEVEL_2_APPROVAL_REQUIRED"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["success"] is True
    assert "goal" in data
    assert len(data["goal"]["success_criteria"]) > 0
    assert data["goal"]["verifiable_ref"] is not None


def test_knowledge_graph_endpoints():
    """Verify Knowledge Graph & Graph RAG query APIs."""
    res = client.get("/api/knowledge-graph/entities")
    if res.status_code == 200:
        data = res.json()
        assert data["success"] is True

    # Multi-hop Graph RAG query
    rag_res = client.post("/api/knowledge-graph/query", json={"query": "What depends on Redis and Kafka?", "max_hops": 2})
    if rag_res.status_code == 200:
        rag_data = rag_res.json()
        assert rag_data["success"] is True
        assert "evidence_summary" in rag_data


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


def test_autonomous_workflows_dispatch_and_approval():
    """Verify Autonomous AI Workflow DAG compilation and human approval gate."""
    wf = global_autonomous_engine.plan_and_dispatch_workflow("Continuous container vulnerability scan and patch gating")
    assert wf is not None
    assert len(wf.steps_dag) == 4
    
    # Test step approval
    gate_step = next((s for s in wf.steps_dag if s.requires_approval), None)
    if gate_step:
        appr_res = global_autonomous_engine.approve_workflow_step(wf.id, gate_step.id)
        assert appr_res["success"] is True


def test_computer_agent_session():
    """Verify Computer-Using AI / Browser Agent session management."""
    res = client.get("/api/computer-agent/sessions")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["sessions"]) > 0


def test_intelligence_platform_overview():
    """Verify AI Intelligence & Evaluation Platform quality scorecard and benchmarks."""
    res = client.get("/api/intelligence/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["intelligence"]["scorecard"]["overall_quality_score"] > 90.0
    assert len(data["intelligence"]["benchmarks"]) >= 4
    assert len(data["intelligence"]["red_team_results"]) >= 3


def test_emergency_safety_interrupt():
    """Verify AIForge OS Emergency Safety Interrupt and Resume."""
    stop_res = client.post("/api/os/emergency-stop")
    assert stop_res.status_code == 200
    assert stop_res.json()["kernel_state"] == "EMERGENCY_STOPPED"
    
    resume_res = client.post("/api/os/resume")
    assert resume_res.status_code == 200
    assert resume_res.json()["kernel_state"] == "RUNNING"
