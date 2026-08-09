"""
Unit tests for Production-Grade & Research-Level AIForge V2 Platform Infrastructure
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import unittest
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


class TestProductionGradePlatform(unittest.TestCase):

    def test_mcp_server_discovery_and_execution(self):
        mcp = MCPServer()
        tools = mcp.list_tools()
        self.assertGreaterEqual(len(tools), 5)
        res = mcp.call_tool("postgres_query", {"sql": "SELECT 1"})
        self.assertEqual(res["jsonrpc"], "2.0")

    def test_litellm_and_vllm(self):
        litellm = LiteLLMGateway()
        res = litellm.completion(model="ollama/qwen2.5-coder", messages=[{"role": "user", "content": "hello"}])
        self.assertEqual(res["provider"], "Ollama")

        vllm = VLLMEngine()
        batch_res = vllm.generate_batch(["Prompt 1", "Prompt 2"])
        self.assertEqual(len(batch_res), 2)

    def test_durable_workflow(self):
        wf = DurableWorkflowEngine()
        state = wf.start_workflow("wf_unit_test", "Build e-commerce")
        self.assertEqual(state["status"], "RUNNING")

    def test_graph_and_qdrant(self):
        graph = Neo4jKnowledgeGraph()
        topo = graph.get_full_topology()
        self.assertGreaterEqual(topo["nodes_count"], 5)

        qdrant = QdrantVectorStore()
        hits = qdrant.search_vectors("FastAPI")
        self.assertGreaterEqual(len(hits), 1)

    def test_opa_security_and_telemetry(self):
        opa = OPAPolicyEngine()
        pol = opa.evaluate_policy({"action": "generate_code", "role": "developer", "code": "def ok(): pass"})
        self.assertTrue(pol["is_allowed"])

        telemetry = TelemetryEngine()
        span = telemetry.start_span("agent_test")
        telemetry.end_span(span)
        prom = telemetry.get_prometheus_metrics()
        self.assertIn("aiforge_agent_spans_total", prom)

    def test_deepeval_framework(self):
        eval_fw = DeepEvalFramework()
        res = eval_fw.evaluate_generation("Build React App", "import React from 'react';")
        self.assertGreaterEqual(res["overall_quality_score"], 80.0)


if __name__ == "__main__":
    unittest.main()
