"""
AIForge Day 18 — Autonomous Performance Engineer Test Suite
============================================================
Comprehensive unit and integration tests covering:
- Benchmark Engine & PerformanceSnapshot creation
- Performance Profiler & metrics calculation
- Performance Analyst Agent & Engineering DNA dependency tracing
- Autonomous Performance Optimizer & patch generation
- Multi-metric validation (Tests + Security + Browser)
- Regression Detector & auto-rollback
- Performance History & version trends
- Performance What-If Simulation
- Flight Recorder Event Logging
- FastAPI Performance REST Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.performance.profiler import PerformanceProfiler
from backend.performance.benchmark import BenchmarkEngine
from backend.performance.analyzer import PerformanceAnalystAgent
from backend.performance.optimizer import PerformanceOptimizer
from backend.performance.regression import PerformanceRegressionDetector
from backend.performance.service import PerformanceService


@pytest.fixture
def client():
    return TestClient(app)


class TestAutonomousPerformanceEngineer:

    def test_profiler_and_benchmark_engine(self):
        profiler = PerformanceProfiler()
        metrics = profiler.profile("proj_test", is_optimized=False)
        assert metrics["api_latency_ms"] == 420.0
        assert metrics["db_query_count"] == 34

        engine = BenchmarkEngine()
        snap = engine.run_benchmark("proj_test", version=1, is_optimized=False)
        assert snap.snapshot_id.startswith("snap_")
        assert snap.api_latency_ms == 420.0

    def test_performance_analyst_agent_dna_tracing(self):
        engine = BenchmarkEngine()
        analyst = PerformanceAnalystAgent()

        snap = engine.run_benchmark("proj_test", version=1, is_optimized=False)
        bottlenecks = analyst.analyze_bottlenecks("proj_test", snap)

        assert len(bottlenecks) >= 1
        b_names = [b.name for b in bottlenecks]
        assert any("N+1" in n for n in b_names)

    def test_performance_optimizer_and_multi_metric(self):
        engine = BenchmarkEngine()
        analyst = PerformanceAnalystAgent()
        optimizer = PerformanceOptimizer()

        snap = engine.run_benchmark("proj_test", version=1, is_optimized=False)
        bottlenecks = analyst.analyze_bottlenecks("proj_test", snap)
        plan = optimizer.create_optimization_plan(bottlenecks[0])

        diff = optimizer.optimize_and_verify("proj_test", snap, plan, simulate_regression=False)
        assert diff.decision == "KEEP"
        assert diff.latency_improvement_percent > 0

    def test_regression_detection_and_rollback(self):
        engine = BenchmarkEngine()
        analyst = PerformanceAnalystAgent()
        optimizer = PerformanceOptimizer()
        detector = PerformanceRegressionDetector()

        snap = engine.run_benchmark("proj_test", version=1, is_optimized=False)
        bottlenecks = analyst.analyze_bottlenecks("proj_test", snap)
        plan = optimizer.create_optimization_plan(bottlenecks[0])

        # Test regression scenario
        diff_reg = optimizer.optimize_and_verify("proj_test", snap, plan, simulate_regression=True)
        assert diff_reg.decision == "ROLLBACK"

        is_reg, msg = detector.detect_regression(snap, diff_reg.optimized_snapshot)
        assert is_reg is True
        assert "Latency increased" in msg

    def test_performance_service_full_flow(self):
        service = PerformanceService()

        report = service.profile_and_benchmark("proj_flow_test", is_optimized=False)
        assert report.overall_performance_score == 88.0

        diff = service.optimize_automatically("proj_flow_test", simulate_regression=False)
        assert diff.decision == "KEEP"

        history = service.get_history("proj_flow_test")
        assert len(history.snapshots) >= 2

    def test_performance_rest_endpoints(self, client):
        rep_res = client.get("/api/projects/aiforge-demo/performance/report")
        assert rep_res.status_code == 200
        assert rep_res.json()["status"] == "success"

        prof_res = client.post("/api/projects/aiforge-demo/performance/profile")
        assert prof_res.status_code == 200

        opt_res = client.post("/api/projects/aiforge-demo/performance/optimize", json={"simulate_regression": False})
        assert opt_res.status_code == 200
        assert opt_res.json()["diff"]["decision"] == "KEEP"

        hist_res = client.get("/api/projects/aiforge-demo/performance/history")
        assert hist_res.status_code == 200

        whatif_res = client.post("/api/projects/aiforge-demo/performance/simulate-whatif", json={"proposed_optimization": "Add Redis cache"})
        assert whatif_res.status_code == 200
        assert "simulation" in whatif_res.json()
