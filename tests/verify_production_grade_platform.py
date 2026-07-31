"""
AIForge V2 Master Verification Suite: Production-Grade & Research-Level Platform Architecture
==============================================================================================
Validates all 10 Top-Priority Platform Pillars:
1. Model Context Protocol (MCP) Server Infrastructure
2. LiteLLM Unified Gateway & High-Performance vLLM Engine
3. Temporal Durable Fault-Tolerant Workflow Engine
4. Neo4j Knowledge Graph Reasoning Engine
5. Qdrant HNSW Vector Search Engine
6. Tree-sitter AST & CodeBERT Semantic Code Search
7. OPA (Open Policy Agent) Enterprise Security Engine
8. OpenTelemetry Tracing & Prometheus Metrics Export
9. DeepEval / Ragas Quality Evaluation & MLflow Tracking
10. Advanced Agent Suite (Debate Agent & Research Agent)
"""

import sys
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.tools.mcp_server import MCPServer
from backend.llm.litellm_gateway import LiteLLMGateway
from backend.llm.vllm_engine import VLLMEngine
from backend.workflow.durable_workflow import DurableWorkflowEngine
from backend.knowledge.graph_knowledge import Neo4jKnowledgeGraph
from backend.rag.qdrant_store import QdrantVectorStore
from backend.quality.semantic_code_search import SemanticCodeSearchEngine
from backend.security.opa_engine import OPAPolicyEngine
from backend.monitoring.telemetry import TelemetryEngine
from backend.evaluation.deepeval_framework import DeepEvalFramework
from backend.agents.debate_agent import DebateAgent
from backend.agents.research_agent import ResearchAgent

PASS = "[PASS]"
FAIL = "[FAIL]"
_results = {"passed": 0, "failed": 0}


def section(title: str):
    print(f"\n{'='*75}")
    print(f"  {title}")
    print(f"{'='*75}")


def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    if condition:
        _results["passed"] += 1
    else:
        _results["failed"] += 1
    msg = f"  {status}  {name}"
    if detail:
        msg += f"\n        => {detail}"
    print(msg)
    return condition


def verify_production_grade_platform():
    print("===========================================================================")
    print(" 🚀 AIForge V2 – Production-Grade & Research-Level Platform Architecture")
    print("===========================================================================\n")

    mcp = MCPServer()
    litellm = LiteLLMGateway()
    vllm = VLLMEngine()
    durable_wf = DurableWorkflowEngine()
    neo4j = Neo4jKnowledgeGraph()
    qdrant = QdrantVectorStore()
    semantic_search = SemanticCodeSearchEngine()
    opa = OPAPolicyEngine()
    telemetry = TelemetryEngine()
    deepeval = DeepEvalFramework()
    debate = DebateAgent()
    research = ResearchAgent()

    # ---------------------------------------------------------
    # Pillar 1: Model Context Protocol (MCP) Server Infrastructure
    # ---------------------------------------------------------
    section("Pillar 1: Model Context Protocol (MCP) Server Infrastructure")
    mcp_tools = mcp.list_tools()
    mcp_call = mcp.call_tool("postgres_query", {"sql": "SELECT * FROM users;"})
    check("Discovered universal MCP tools (GitHub, Postgres, Docker, FS, Terminal, Slack, Jira, AWS)", len(mcp_tools) >= 8)
    check("Executed MCP tool call via JSON-RPC 2.0 protocol", mcp_call.get("jsonrpc") == "2.0" and mcp_call.get("result", {}).get("status") == "SUCCESS")

    # ---------------------------------------------------------
    # Pillar 2: LiteLLM Unified Gateway & vLLM Engine
    # ---------------------------------------------------------
    section("Pillar 2: LiteLLM Gateway & vLLM High-Performance Local Engine")
    llm_res = litellm.completion(model="ollama/qwen2.5-coder", messages=[{"role": "user", "content": "Write React App"}])
    vllm_batch = vllm.generate_batch(["Prompt 1: React UI", "Prompt 2: FastAPI Backend"])
    check("LiteLLM completion across multi-provider specs with cost estimation", "metrics" in llm_res and llm_res["provider"] == "Ollama")
    check("High-throughput vLLM PagedAttention batch generation", len(vllm_batch) == 2 and vllm_batch[0]["throughput_tok_per_sec"] > 50)

    # ---------------------------------------------------------
    # Pillar 3: Temporal Durable Fault-Tolerant Workflows
    # ---------------------------------------------------------
    section("Pillar 3: Temporal Durable Fault-Tolerant Workflows")
    wf_state = durable_wf.start_workflow("wf_prod_01", "Build e-commerce system")
    act_res = durable_wf.execute_activity_with_retry("wf_prod_01", "Frontend_Gen", lambda: "App.jsx created")
    recovered = durable_wf.recover_workflow("wf_prod_01")
    check("Initialized durable workflow session with checkpoints", wf_state["status"] == "RUNNING" and len(wf_state["checkpoints"]) >= 2)
    check("Executed activity with durable retry policy", act_res["status"] == "SUCCESS")
    check("Recovered workflow state from checkpoint persistence", recovered["status"] == "RECOVERED_AND_RUNNING")

    # ---------------------------------------------------------
    # Pillar 4: Neo4j Knowledge Graph Reasoning
    # ---------------------------------------------------------
    section("Pillar 4: Neo4j Knowledge Graph Reasoning")
    topo = neo4j.get_full_topology()
    reasoning = neo4j.reason_over_entity("proj_core")
    check("Constructed Neo4j graph topology (Project -> Arch -> Services -> APIs -> DB -> Deployment)", topo["nodes_count"] >= 6 and topo["edges_count"] >= 5)
    check("Reasoned over graph dependencies and entity relationships", reasoning["relationships_count"] >= 2)

    # ---------------------------------------------------------
    # Pillar 5: Qdrant HNSW Vector Search Engine
    # ---------------------------------------------------------
    section("Pillar 5: Qdrant HNSW Vector Search Engine")
    q_hits = qdrant.search_vectors("FastAPI App", limit=3)
    check("Executed HNSW vector search in Qdrant collection", len(q_hits) >= 1 and q_hits[0]["score"] > 0.0)

    # ---------------------------------------------------------
    # Pillar 6: Tree-sitter AST & CodeBERT Semantic Code Search
    # ---------------------------------------------------------
    section("Pillar 6: Tree-sitter AST & CodeBERT Semantic Code Search")
    sample_code = "import React from 'react';\nfunction AppHeader() { return <h1>Header</h1>; }"
    ast_symbols = semantic_search.parse_ast_symbols(sample_code, "AppHeader.jsx")
    search_hits = semantic_search.search_codebert("Header", {"AppHeader.jsx": sample_code})
    check("Extracted Tree-sitter AST symbols (functions, classes, imports)", ast_symbols["functions_count"] >= 1)
    check("Performed CodeBERT semantic code search across workspace files", len(search_hits) >= 1)

    # ---------------------------------------------------------
    # Pillar 7: OPA Enterprise Security Policy Engine
    # ---------------------------------------------------------
    section("Pillar 7: OPA Enterprise Security Policy Engine")
    pol1 = opa.evaluate_policy({"action": "generate_code", "role": "developer", "code": "def ok(): pass"})
    pol2 = opa.evaluate_policy({"action": "generate_code", "role": "developer", "code": "api_key = '12345_SECRET'"})
    check("Allowed safe code under OPA policy evaluation", pol1["is_allowed"])
    check("Blocked hardcoded secret plaintext under OPA security rule", not pol2["is_allowed"] and pol2["violations_count"] >= 1)

    # ---------------------------------------------------------
    # Pillar 8: OpenTelemetry & Prometheus Metrics Export
    # ---------------------------------------------------------
    section("Pillar 8: OpenTelemetry Tracing & Prometheus Export")
    span = telemetry.start_span("agent_execution_span")
    telemetry.end_span(span)
    prom_metrics = telemetry.get_prometheus_metrics()
    check("Created OpenTelemetry execution span and computed duration", span["status"] == "OK" and span["duration_ms"] >= 0)
    check("Exported metrics in standard Prometheus exposition format", "aiforge_agent_spans_total" in prom_metrics)

    # ---------------------------------------------------------
    # Pillar 9: DeepEval Quality Evaluation & MLflow Tracking
    # ---------------------------------------------------------
    section("Pillar 9: DeepEval Evaluation & MLflow Experiment Tracking")
    eval_res = deepeval.evaluate_generation("Build React Dashboard", "import React from 'react'; export default function Dashboard() {}")
    mlflow_run = deepeval.log_mlflow_experiment("Production Evaluation", {"model": "qwen2.5-coder"}, {"quality": eval_res["overall_quality_score"]})
    check("Evaluated correctness, faithfulness, and context relevance", eval_res["passed"] and eval_res["overall_quality_score"] >= 80.0)
    check("Logged experiment metrics and prompt parameters to MLflow", mlflow_run["run_id"].startswith("mlflow_run_"))

    # ---------------------------------------------------------
    # Pillar 10: Advanced Debate Agent & Autonomous Research Agent
    # ---------------------------------------------------------
    section("Pillar 10: Advanced Debate & Research Agents")
    research_res = research.conduct_research("E-Commerce Microservices")
    debate_res = debate.run_debate("Create Auth Service", [
        {"model": "qwen2.5-coder", "output": "import React from 'react';"},
        {"model": "deepseek-coder", "output": "from fastapi import FastAPI"}
    ])
    check("Autonomous Research Agent conducted pre-coding dependency & spec research", len(research_res["findings"]) >= 2)
    check("Multi-Model Debate Agent critiqued solutions and selected debate winner", debate_res["debate_winner"] is not None)

    # Summary
    print("\n" + "="*75)
    print(f" AIFORGE V2 MASTER PLATFORM VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*75 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = verify_production_grade_platform()
    sys.exit(0 if success else 1)
