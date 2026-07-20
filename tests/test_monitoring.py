# pyrefly: ignore [missing-import]
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from backend.monitoring.metrics_collector import MetricsCollector
from backend.monitoring.health_checker import HealthChecker
from backend.monitoring.incident_detector import IncidentDetector, Incident
from backend.monitoring.root_cause import RootCauseAnalyzer
from backend.monitoring.recovery_engine import RecoveryEngine
from backend.monitoring.validator import RecoveryValidator
from backend.monitoring.autoscaler import AutoScaler
from backend.monitoring.predictor import FailurePredictor
from backend.monitoring.alert_manager import AlertManager
from backend.monitoring.knowledge_base import IncidentKnowledgeBase
from backend.monitoring.analytics import OperationsAnalytics
from backend.monitoring.monitor import OpsMonitor
from backend.monitoring.scheduler import OpsScheduler

def test_metrics_collector():
    collector = MetricsCollector()
    collector.record_request(120.0, is_error=False)
    collector.record_request(500.0, is_error=True)
    collector.record_database_query(5.5)
    collector.record_ai_inference(1500.0)
    collector.set_active_sessions(12)

    snapshot = collector.collect_metrics()
    assert "infrastructure" in snapshot
    assert "containers" in snapshot
    assert "application" in snapshot
    
    app_stats = snapshot["application"]
    assert app_stats["active_sessions"] == 12
    assert app_stats["error_rate_pct"] == 50.0
    assert app_stats["response_time_ms"] == 310.0
    assert app_stats["db_query_time_ms"] == 5.5
    assert app_stats["ai_inference_latency_ms"] == 1500.0

@pytest.mark.anyio
async def test_health_checker():
    checker = HealthChecker()
    
    # Mock checks
    checker.check_api_endpoint = AsyncMock(return_value={"status": "Healthy", "latency_ms": 15.0})
    checker.check_database = AsyncMock(return_value={"status": "Healthy", "latency_ms": 1.0})
    checker.check_redis = AsyncMock(return_value={"status": "Healthy", "latency_ms": 0.5})
    checker.check_ollama = AsyncMock(return_value={"status": "Healthy"})
    checker.check_ssl_and_dns = AsyncMock(return_value={"status": "Healthy"})

    report = await checker.run_comprehensive_check()
    assert report["health_score"] == 100
    
    # Degrade API and verify score drops
    checker.check_api_endpoint = AsyncMock(return_value={"status": "Unhealthy", "error": "500"})
    report2 = await checker.run_comprehensive_check()
    assert report2["health_score"] == 70

def test_incident_detector():
    detector = IncidentDetector()
    
    # Simulated metrics (Normal)
    metrics_normal = {
        "infrastructure": {"cpu_utilization": 45.0, "memory_utilization": 50.0, "disk_utilization": 20.0},
        "application": {"response_time_ms": 120.0, "error_rate_pct": 0.0}
    }
    health_normal = {
        "checks": {"api": {"status": "Healthy"}, "database": {"status": "Healthy"}, "redis": {"status": "Healthy"}, "ollama": {"status": "Healthy"}}
    }
    
    incidents = detector.detect_incidents(metrics_normal, health_normal)
    assert len(incidents) == 0

    # Simulated metrics (Unhealthy)
    metrics_bad = {
        "infrastructure": {"cpu_utilization": 95.0, "memory_utilization": 92.0, "disk_utilization": 99.0},
        "application": {"response_time_ms": 3200.0, "error_rate_pct": 20.0}
    }
    health_bad = {
        "checks": {"api": {"status": "Unhealthy"}, "database": {"status": "Unhealthy"}, "redis": {"status": "Healthy"}, "ollama": {"status": "Healthy"}}
    }

    incidents_bad = detector.detect_incidents(metrics_bad, health_bad)
    signatures = [i.signature for i in incidents_bad]
    
    assert "high_cpu" in signatures
    assert "memory_leak" in signatures
    assert "disk_exhaustion" in signatures
    assert "api_downtime" in signatures
    assert "db_connection_failure" in signatures
    assert "slow_responses" in signatures
    assert "high_error_rate" in signatures

def test_root_cause_fallback():
    from unittest.mock import patch
    analyzer = RootCauseAnalyzer()
    # If LLM raises error/timeout, SRE agent falls back safely
    with patch("backend.monitoring.root_cause.generate_text", side_effect=Exception("Timeout")):
        res = analyzer.analyze(
            incidents=[{"signature": "db_connection_failure", "severity": "Critical", "description": "Failed to connect", "service": "Database Engine"}],
            metrics={},
            health={}
        )
    assert res["incident"] == "db_connection_failure"
    assert res["recommended_action"] == "Restart Database"

def test_recovery_engine(tmp_path):
    kb_file = tmp_path / "incident_kb.json"
    kb = IncidentKnowledgeBase(file_path=str(kb_file))
    engine = RecoveryEngine(knowledge_base=kb)
    
    recommendation = {"recommended_action": "Restart Database", "confidence": 0.95}
    strat, dur = engine.execute_recovery("db_connection_failure", recommendation)
    assert strat == "Restart Database"
    assert dur > 0.0

@pytest.mark.anyio
async def test_recovery_validator():
    health_checker = HealthChecker()
    health_checker.run_comprehensive_check = AsyncMock(return_value={"health_score": 90, "checks": {}})
    validator = RecoveryValidator(health_checker)
    success, log = await validator.validate_recovery()
    assert success is True
    assert "System Health Score: 90/100" in log

def test_autoscaler():
    scaler = AutoScaler(cpu_threshold=80.0, mem_threshold=85.0)
    
    metrics = {
        "infrastructure": {"cpu_utilization": 85.0, "memory_utilization": 90.0},
        "application": {"queue_depth": 0}
    }
    
    decisions = scaler.evaluate_scaling(metrics)
    actions = [d["action"] for d in decisions]
    assert "horizontal" in actions
    assert "vertical" in actions

def test_predictor():
    predictor = FailurePredictor(prediction_window_seconds=10.0)
    
    # 5 simulated history items showing a steep increase in memory usage
    history = [
        {"timestamp": 100, "infrastructure": {"cpu_utilization": 50, "memory_utilization": 70, "disk_utilization": 10}, "application": {}},
        {"timestamp": 102, "infrastructure": {"cpu_utilization": 50, "memory_utilization": 75, "disk_utilization": 10}, "application": {}},
        {"timestamp": 104, "infrastructure": {"cpu_utilization": 50, "memory_utilization": 80, "disk_utilization": 10}, "application": {}},
        {"timestamp": 106, "infrastructure": {"cpu_utilization": 50, "memory_utilization": 85, "disk_utilization": 10}, "application": {}},
        {"timestamp": 108, "infrastructure": {"cpu_utilization": 50, "memory_utilization": 90, "disk_utilization": 10}, "application": {}},
    ]
    
    predictions = predictor.predict_failures(history)
    assert len(predictions) > 0
    assert predictions[0]["metric"] == "Memory Usage"
    assert predictions[0]["severity"] == "Critical"

def test_alert_manager():
    manager = AlertManager(active_channels=["slack", "email"])
    alert = manager.dispatch_alert("high_cpu", "Critical", "Host System", "CPU is at 95%")
    assert alert["incident"] == "high_cpu"
    assert alert["status"] == "Active"

def test_analytics():
    analytics = OperationsAnalytics()
    history = [
        {"signature": "high_cpu", "root_cause": "Busy process", "strategy": "Scale Replicas", "success": True, "duration_seconds": 10.0},
        {"signature": "db_down", "root_cause": "Disk full", "strategy": "Restart DB", "success": False, "duration_seconds": 20.0}
    ]
    
    metrics = analytics.calculate_metrics(history, scaling_events_count=2)
    assert metrics["total_incidents"] == 2
    assert metrics["recovery_success_rate_pct"] == 50.0
    assert metrics["mttr_seconds"] == 10.0
    assert metrics["autoscaling_events_count"] == 2

@pytest.mark.anyio
async def test_ops_monitor_and_scheduler(tmp_path):
    kb_file = tmp_path / "incident_kb.json"
    monitor = OpsMonitor(kb_file_path=str(kb_file))
    
    # Mock checks to simulate a healthy state
    monitor.health_checker.run_comprehensive_check = AsyncMock(return_value={"health_score": 100, "checks": {}})
    
    outcome = await monitor.execute_operations_step()
    assert outcome["health_score"] == 100
    assert len(outcome["active_incidents"]) == 0

    # Start and Stop scheduler
    scheduler = OpsScheduler(monitor)
    scheduler.start()
    assert scheduler.running is True
    await asyncio.sleep(0.1)
    scheduler.stop()
    assert scheduler.running is False
