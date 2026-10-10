"""
AIForge Phase 3: Specialized Agent Registry & Capability Engine
===============================================================
Defines and registers specialized autonomous AI agents:
- Research Agent, Coding Agent, Data Analyst Agent, Document Agent,
  Security Agent (Defensive), and Verifier Agent.
Each agent declares tool allowlists, risk levels, and permission boundaries.
"""

import time
import uuid
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field

_logger = logging.getLogger("aiforge.multi_agent.registry")


class AgentSpecialty(str, Enum):
    RESEARCH = "RESEARCH"
    CODING = "CODING"
    DATA_ANALYST = "DATA_ANALYST"
    DOCUMENT = "DOCUMENT"
    SECURITY = "SECURITY"
    VERIFIER = "VERIFIER"


class AgentDefinition(BaseModel):
    id: str
    name: str
    specialty: AgentSpecialty
    description: str
    capabilities: List[str]
    allowed_tools: List[str]
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH
    model_preference: str = "claude-3-5-sonnet"
    is_active: bool = True


BUILTIN_AGENTS = [
    AgentDefinition(
        id="agent_researcher",
        name="Research Specialist Agent",
        specialty=AgentSpecialty.RESEARCH,
        description="Gathers evidence from Graph RAG, RFCs, and authoritative technical web sources.",
        capabilities=["web_research", "graph_rag", "evidence_extraction", "fact_verification"],
        allowed_tools=["web_search", "document_analyzer", "file_search"],
        risk_level="LOW",
        model_preference="claude-3-5-sonnet"
    ),
    AgentDefinition(
        id="agent_coder",
        name="Lead Coding Agent",
        specialty=AgentSpecialty.CODING,
        description="Performs AST code analysis, sandbox test runner execution, and atomic refactoring.",
        capabilities=["code_analysis", "test_runner", "sandbox_execution", "ast_refactor"],
        allowed_tools=["code_execution", "file_reader", "file_search"],
        risk_level="HIGH",
        model_preference="claude-3-5-sonnet"
    ),
    AgentDefinition(
        id="agent_data_analyst",
        name="Data & Statistical Analyst",
        specialty=AgentSpecialty.DATA_ANALYST,
        description="Parses JSON/CSV datasets, computes distributions, percentiles, and telemetry anomalies.",
        capabilities=["dataset_parsing", "statistical_modeling", "latency_analytics"],
        allowed_tools=["data_analyzer", "calculator"],
        risk_level="MEDIUM",
        model_preference="deepseek-r1"
    ),
    AgentDefinition(
        id="agent_document_writer",
        name="Technical Document Agent",
        specialty=AgentSpecialty.DOCUMENT,
        description="Synthesizes structured architecture RFCs, executive deliverables, and cited reports.",
        capabilities=["document_synthesis", "markdown_rfc", "provenance_compilation"],
        allowed_tools=["document_analyzer", "file_reader"],
        risk_level="LOW",
        model_preference="claude-3-5-sonnet"
    ),
    AgentDefinition(
        id="agent_security_auditor",
        name="Defensive Security Agent",
        specialty=AgentSpecialty.SECURITY,
        description="Defensively analyzes access controls, JWT signatures, injection boundaries, and CVEs.",
        capabilities=["vulnerability_triage", "attack_path_analysis", "prompt_defense", "rbac_audit"],
        allowed_tools=["file_reader", "file_search", "document_analyzer"],
        risk_level="MEDIUM",
        model_preference="claude-3-5-sonnet"
    ),
    AgentDefinition(
        id="agent_verifier",
        name="Consensus Verification Judge",
        specialty=AgentSpecialty.VERIFIER,
        description="Cross-verifies claims, tests evidence citations, detects contradictions, and grades consensus.",
        capabilities=["consensus_grading", "citation_audit", "peer_review_arbitration"],
        allowed_tools=["calculator", "file_reader"],
        risk_level="LOW",
        model_preference="claude-3-5-sonnet"
    )
]


class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, AgentDefinition] = {a.id: a for a in BUILTIN_AGENTS}

    def list_agents(self) -> List[AgentDefinition]:
        return list(self._agents.values())

    def get_agent(self, agent_id: str) -> Optional[AgentDefinition]:
        return self._agents.get(agent_id)

    def find_capable_agents(self, capability: str) -> List[AgentDefinition]:
        return [a for a in self._agents.values() if capability in a.capabilities and a.is_active]

    def register_agent(self, agent: AgentDefinition):
        self._agents[agent.id] = agent


global_multi_agent_registry = AgentRegistry()
