"""
FastAPI Routes for Production-Grade & Research-Level AIForge V2 Platform Architecture
========================================================================================
Exposes REST APIs for MCP Server, LiteLLM + vLLM, Durable Temporal Workflows, Neo4j Knowledge Graph, Qdrant Vector Search, Tree-sitter + CodeBERT, OPA Security, OpenTelemetry, DeepEval, Debate Agent, and Research Agent.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from backend.tools.mcp_server import global_mcp_server
from backend.llm.litellm_gateway import global_litellm_gateway
from backend.llm.vllm_engine import global_vllm_engine
from backend.workflow.durable_workflow import global_durable_workflow
from backend.knowledge.graph_knowledge import global_neo4j_graph
from backend.rag.qdrant_store import global_qdrant_store
from backend.quality.semantic_code_search import global_semantic_code_search
from backend.security.opa_engine import global_opa_policy_engine
from backend.monitoring.telemetry import global_telemetry_engine
from backend.evaluation.deepeval_framework import global_deepeval_framework
from backend.agents.debate_agent import global_debate_agent
from backend.agents.research_agent import global_research_agent

router = APIRouter(tags=["Production-Grade Platform Architecture"])


class MCPCallInput(BaseModel):
    tool_name: str
    params: Optional[Dict[str, Any]] = None


class LiteLLMInput(BaseModel):
    model: Optional[str] = "ollama/qwen2.5-coder"
    prompt: str


class VLLMBatchInput(BaseModel):
    prompts: List[str]


class DurableWorkflowInput(BaseModel):
    workflow_id: str
    prompt: str


class GraphReasonInput(BaseModel):
    entity_id: str


class QdrantSearchInput(BaseModel):
    query: str
    limit: Optional[int] = 5


class SemanticSearchInput(BaseModel):
    query: str
    workspace_files: Dict[str, str]


class OPAPolicyInput(BaseModel):
    action: str
    role: str
    code: Optional[str] = ""


class DeepEvalInput(BaseModel):
    prompt: str
    generated_code: str
    context: Optional[str] = None


class DebateInput(BaseModel):
    task_prompt: str
    candidates: List[Dict[str, Any]]


class ResearchInput(BaseModel):
    topic: str


# 1. Model Context Protocol (MCP) Server
@router.get("/api/v1/mcp/tools")
@router.get("/mcp/tools")
async def list_mcp_tools():
    """Returns registered universal MCP tools."""
    return {"status": "success", "tools": global_mcp_server.list_tools()}


@router.post("/api/v1/mcp/call")
@router.post("/mcp/call")
async def call_mcp_tool(req: MCPCallInput):
    """Executes registered MCP tool via JSON-RPC protocol."""
    res = global_mcp_server.call_tool(req.tool_name, req.params or {})
    return res


# 2. LiteLLM Unified Gateway & vLLM Batch Engine
@router.post("/api/v1/litellm/completion")
@router.post("/litellm/completion")
async def litellm_completion(req: LiteLLMInput):
    """Unified LLM completion across OpenAI, Anthropic, Gemini, Ollama, Groq, DeepSeek."""
    res = global_litellm_gateway.completion(
        model=req.model or "ollama/qwen2.5-coder",
        messages=[{"role": "user", "content": req.prompt}]
    )
    return {"status": "success", "response": res}


@router.post("/api/v1/vllm/batch")
@router.post("/vllm/batch")
async def vllm_batch_generation(req: VLLMBatchInput):
    """High-throughput local vLLM / Ollama PagedAttention batch generation."""
    res = global_vllm_engine.generate_batch(req.prompts)
    return {"status": "success", "batch_results": res}


# 3. Durable Temporal Workflows
@router.post("/api/v1/workflow/durable")
@router.post("/workflow/durable")
async def execute_durable_workflow(req: DurableWorkflowInput):
    """Starts or recovers a stateful durable workflow."""
    res = global_durable_workflow.start_workflow(req.workflow_id, req.prompt)
    return {"status": "success", "workflow_state": res}


# 4. Neo4j Graph & Qdrant Vector Stores
@router.get("/api/v1/graph/topology")
@router.get("/graph/topology")
async def get_graph_topology():
    """Retrieves Neo4j Knowledge Graph topology."""
    return {"status": "success", "graph": global_neo4j_graph.get_full_topology()}


@router.post("/api/v1/graph/reason")
@router.post("/graph/reason")
async def reason_graph(req: GraphReasonInput):
    """Reasons over graph dependencies for a specific entity."""
    res = global_neo4j_graph.reason_over_entity(req.entity_id)
    return {"status": "success", "reasoning": res}


@router.post("/api/v1/rag/qdrant-search")
@router.post("/rag/qdrant-search")
async def search_qdrant(req: QdrantSearchInput):
    """Executes HNSW vector search in Qdrant vector database."""
    res = global_qdrant_store.search_vectors(req.query, limit=req.limit or 5)
    return {"status": "success", "vector_hits": res}


# 5. Semantic Code Search (Tree-sitter + CodeBERT)
@router.post("/api/v1/quality/semantic-search")
@router.post("/quality/semantic-search")
async def semantic_code_search(req: SemanticSearchInput):
    """Performs Tree-sitter AST symbol parsing and CodeBERT semantic code search."""
    res = global_semantic_code_search.search_codebert(req.query, req.workspace_files)
    return {"status": "success", "search_results": res}


# 6. OPA Security Policy Engine
@router.post("/api/v1/security/opa-policy")
@router.post("/security/opa-policy")
async def evaluate_opa_policy(req: OPAPolicyInput):
    """Evaluates Open Policy Agent (OPA) authorization and safety rules."""
    res = global_opa_policy_engine.evaluate_policy(
        input_context={"action": req.action, "role": req.role, "code": req.code or ""}
    )
    return {"status": "success", "opa_evaluation": res}


# 7. OpenTelemetry & Prometheus Metrics
@router.get("/api/v1/monitoring/telemetry")
@router.get("/monitoring/telemetry")
async def get_telemetry_spans():
    """Retrieves OpenTelemetry execution spans."""
    return {"status": "success", "spans": global_telemetry_engine.spans}


@router.get("/api/v1/monitoring/prometheus")
@router.get("/monitoring/prometheus")
async def export_prometheus_metrics():
    """Exports metrics in standard Prometheus exposition format."""
    metrics_text = global_telemetry_engine.get_prometheus_metrics()
    return {"status": "success", "prometheus_format": metrics_text}


# 8. DeepEval Evaluation & MLflow Tracker
@router.post("/api/v1/evaluation/deepeval")
@router.post("/evaluation/deepeval")
async def evaluate_deepeval(req: DeepEvalInput):
    """Evaluates generation quality via DeepEval / Ragas metrics and logs MLflow experiment."""
    eval_res = global_deepeval_framework.evaluate_generation(req.prompt, req.generated_code, req.context)
    mlflow_res = global_deepeval_framework.log_mlflow_experiment(
        experiment_name="AIForge Quality Benchmark",
        params={"model": "qwen2.5-coder", "prompt_len": len(req.prompt)},
        metrics={"quality_score": eval_res["overall_quality_score"], "correctness": eval_res["correctness_score"]}
    )
    return {"status": "success", "evaluation": eval_res, "mlflow": mlflow_res}


# 9. Debate Agent & Research Agent
@router.post("/api/v1/agents/debate")
@router.post("/agents/debate")
async def run_agent_debate(req: DebateInput):
    """Orchestrates multi-model debate competition between candidate solutions."""
    res = global_debate_agent.run_debate(req.task_prompt, req.candidates)
    return {"status": "success", "debate": res}


@router.post("/api/v1/agents/research")
@router.post("/agents/research")
async def run_agent_research(req: ResearchInput):
    """Runs autonomous technical research prior to code generation."""
    res = global_research_agent.conduct_research(req.topic)
    return {"status": "success", "research": res}
