import time
import logging
from typing import Dict, Any

_logger = logging.getLogger("aiforge.plugins")

class PluginMonitor:
    """
    Monitors latency trends, error rates, invocations, and health of active plugins.
    """

    def __init__(self) -> None:
        self.metrics: Dict[str, Dict[str, Any]] = {}

    def start_invocation(self, name: str) -> float:
        return time.perf_counter()

    def record_metrics(self, name: str, start_time: float, success: bool, memory_peak_kb: float = 0.0) -> None:
        name_clean = name.lower().strip()
        elapsed = (time.perf_counter() - start_time) * 1000.0  # in ms
        
        if name_clean not in self.metrics:
            self.metrics[name_clean] = {
                "invocations": 0,
                "crashes": 0,
                "execution_time_total_ms": 0.0,
                "average_time_ms": 0.0,
                "memory_peak_kb": 0.0,
                "success_rate": 100.0
            }

        m = self.metrics[name_clean]
        m["invocations"] += 1
        if not success:
            m["crashes"] += 1
        
        m["execution_time_total_ms"] += elapsed
        m["average_time_ms"] = m["execution_time_total_ms"] / m["invocations"]
        m["memory_peak_kb"] = max(m["memory_peak_kb"], memory_peak_kb)
        
        successes = m["invocations"] - m["crashes"]
        m["success_rate"] = (successes / m["invocations"]) * 100.0

        _logger.info(f"Plugin '{name}' metrics updated - Invocation time: {elapsed:.2f} ms")

    def get_metrics_for_plugin(self, name: str) -> Dict[str, Any]:
        return self.metrics.get(name.lower().strip(), {
            "invocations": 0,
            "crashes": 0,
            "average_time_ms": 0.0,
            "success_rate": 100.0
        })
