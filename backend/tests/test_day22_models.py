import pytest
from fastapi.testclient import TestClient

from backend.models.registry import ModelRegistry
from backend.models.router import IntelligentRouter
from backend.models.fallback import AutomaticFallbackHandler
from backend.models.consensus import ConsensusEngine
from backend.models.benchmark import ModelBenchmarker
from backend.main import app

client = TestClient(app)


def test_model_registry_capabilities():
    """Test 1: ModelRegistry list models and capability scores."""
    reg = ModelRegistry()

    models = reg.list_models()
    assert len(models) >= 3
    qwen = reg.get_model("qwen2.5-coder")
    assert qwen["capabilities"]["backend"] == 10


def test_intelligent_router():
    """Test 2: IntelligentRouter task-to-model selection rules."""
    router = IntelligentRouter()

    # Planner -> Llama
    res_plan = router.route_task("planner")
    assert res_plan["selected_model"] == "llama3.1"

    # Backend -> Qwen
    res_be = router.route_task("backend")
    assert res_be["selected_model"] == "qwen2.5-coder"

    # Architecture -> DeepSeek
    res_arch = router.route_task("architecture")
    assert res_arch["selected_model"] == "deepseek-coder"

    # User Override
    res_override = router.route_task("backend", user_override="llama3.1")
    assert res_override["selected_model"] == "llama3.1"


def test_automatic_fallback_handler():
    """Test 3: AutomaticFallbackHandler failover from failing model to backup model."""
    fallback = AutomaticFallbackHandler()

    def mock_invoke(m_id):
        if m_id == "failing_model":
            raise RuntimeError("Model timeout")
        return f"Response from {m_id}"

    res = fallback.execute_with_fallback("failing_model", "backend", mock_invoke)
    assert res["status"] == "success"
    assert res["was_fallback"] is True
    assert res["used_model"] != "failing_model"


def test_consensus_engine():
    """Test 4: ConsensusEngine multi-model evaluation and response selection."""
    consensus = ConsensusEngine()

    res = consensus.generate_consensus("Design Database Architecture for Social Media", "architecture")
    assert res["evaluated_models_count"] >= 2
    assert res["confidence_score"] >= 80.0
    assert len(res["best_response"]) > 0


def test_model_benchmarking():
    """Test 5: ModelBenchmarker latency and throughput benchmarking."""
    bench = ModelBenchmarker()

    single = bench.benchmark_model("qwen2.5-coder", sample_tokens=200)
    assert single["latency_seconds"] > 0
    assert single["tokens_per_second"] > 0

    all_res = bench.benchmark_all_models()
    assert all_res["total_models"] >= 3


def test_model_api_endpoints():
    """Test 6: FastAPI Model API routes (/api/models, /api/models/status, /api/models/route, /api/models/consensus)."""
    # 1. Models list
    res_m = client.get("/api/models")
    assert res_m.status_code == 200
    assert "installed" in res_m.json()

    # 2. Status
    res_s = client.get("/api/models/status")
    assert res_s.status_code == 200
    assert res_s.json()["system_health"] == "operational"

    # 3. Route
    res_r = client.post("/api/models/route", json={"task_name": "backend"})
    assert res_r.status_code == 200
    assert res_r.json()["selected_model"] == "qwen2.5-coder"

    # 4. Consensus
    res_c = client.post("/api/models/consensus", json={"prompt": "Design API", "task_name": "architecture"})
    assert res_c.status_code == 200
    assert res_c.json()["confidence_score"] > 0
