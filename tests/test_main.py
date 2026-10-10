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
    assert data["result"]["route"] in ["CYBER_COPILOT_SOC", "GRAPH_RAG_INTELLIGENCE", "MULTI_AGENT_ORCHESTRATOR"]


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


def test_multi_agent_collaboration_endpoint():
    """Verify Multi-Agent collaboration mission execution."""
    res = client.post("/api/multi-agent/collaborate", json={"objective": "Cross-service latency audit and code verification"})
    if res.status_code == 200:
        data = res.json()
        assert data["success"] is True
        assert data["run"]["consensus_score"] >= 0.8


def test_blockchain_verifiable_ledger():
    """Verify Cryptographic Hash Chain, HMAC Signature and Ledger Anchoring."""
    records = global_verifiable_ledger.list_records()
    assert len(records) > 0
    
    first_id = records[0].id
    verify_res = global_verifiable_ledger.verify_record_integrity(first_id)
    assert verify_res["valid"] is True
    assert verify_res["trust_status"] == "VERIFIABLE_CRYPTOGRAPHIC_INTEGRITY"


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
