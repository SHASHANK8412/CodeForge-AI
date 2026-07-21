import pytest
import time
from backend.plugins.monitor import PluginMonitor

def test_monitoring_records():
    monitor = PluginMonitor()
    
    start = monitor.start_invocation("MockPlugin")
    time.sleep(0.01)
    monitor.record_metrics("MockPlugin", start, success=True)

    metrics = monitor.get_metrics_for_plugin("MockPlugin")
    assert metrics["invocations"] == 1
    assert metrics["crashes"] == 0
    assert metrics["success_rate"] == 100.0

    # Test crash scenario
    start = monitor.start_invocation("MockPlugin")
    monitor.record_metrics("MockPlugin", start, success=False)
    metrics = monitor.get_metrics_for_plugin("MockPlugin")
    assert metrics["invocations"] == 2
    assert metrics["crashes"] == 1
    assert metrics["success_rate"] == 50.0
