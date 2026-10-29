import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.sre")


class AutoScaler:
    """
    Turns load metrics into scaling recommendations. AIForge has no orchestrator to scale, so nothing is
    applied: every decision is marked "applied": False, and recommendations are relative to the configured
    baseline (they do not accumulate step after step).
    """

    def __init__(
        self,
        cpu_threshold: float = 80.0,
        mem_threshold: float = 85.0,
        queue_threshold: int = 100,
        baseline_replicas: int = 1,
        baseline_memory_limit_mb: int = 512,
    ) -> None:
        self.cpu_threshold = cpu_threshold
        self.mem_threshold = mem_threshold
        self.queue_threshold = queue_threshold
        self.backend_replicas = baseline_replicas
        self.backend_memory_limit_mb = baseline_memory_limit_mb
        self._last: set = set()

    def evaluate_scaling(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        decisions: List[Dict[str, Any]] = []
        infra = metrics.get("infrastructure", {})
        apps = metrics.get("application", {})
        cpu = infra.get("cpu_utilization", 0.0)
        mem = infra.get("memory_utilization", 0.0)
        queue_len = apps.get("queue_depth", 0)

        def recommend(action, reason, **target):
            decisions.append({"action": action, "service": "backend", "applied": False,
                              "note": "recommendation only: no orchestrator is connected", "reason": reason, **target})

        if cpu >= self.cpu_threshold:
            recommend("horizontal", f"CPU usage ({cpu}%) crossed threshold of {self.cpu_threshold}%", replicas=self.backend_replicas + 1)
        elif queue_len >= self.queue_threshold:
            recommend("horizontal", f"Queue depth ({queue_len}) crossed limit of {self.queue_threshold}", replicas=self.backend_replicas + 1)
        if mem >= self.mem_threshold:
            recommend("vertical", f"Memory usage ({mem}%) crossed threshold of {self.mem_threshold}%",
                      memory_limit_mb=self.backend_memory_limit_mb + 256)

        current = {d["action"] for d in decisions}
        if current - self._last:          # log when a recommendation starts, not on every polling step
            _logger.info("Scaling recommended (not applied): %s", "; ".join(d["reason"] for d in decisions))
        self._last = current
        return decisions
