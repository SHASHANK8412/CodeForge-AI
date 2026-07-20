import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.sre")

class AutoScaler:
    """
    Evaluates system load metrics and generates recommendations for horizontal and vertical scaling.
    """

    def __init__(
        self,
        cpu_threshold: float = 80.0,
        mem_threshold: float = 85.0,
        queue_threshold: int = 100
    ) -> None:
        self.cpu_threshold = cpu_threshold
        self.mem_threshold = mem_threshold
        self.queue_threshold = queue_threshold
        
        # Track simulated current limits
        self.backend_replicas = 1
        self.backend_memory_limit_mb = 512

    def evaluate_scaling(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Processes current telemetry metrics to determine if scaling actions are required.
        """
        decisions: List[Dict[str, Any]] = []
        
        infra = metrics.get("infrastructure", {})
        apps = metrics.get("application", {})

        cpu = infra.get("cpu_utilization", 0.0)
        mem = infra.get("memory_utilization", 0.0)
        queue_len = apps.get("queue_depth", 0)
        req_rate = apps.get("request_rate_tps", 0.0)

        # 1. Horizontal Scaling Check (Replicas addition)
        if cpu >= self.cpu_threshold:
            self.backend_replicas += 1
            decisions.append({
                "action": "horizontal",
                "service": "backend",
                "replicas": self.backend_replicas,
                "reason": f"CPU usage ({cpu}%) crossed threshold of {self.cpu_threshold}%"
            })
            _logger.warning(f"Horizontal scale-up triggered: replicas={self.backend_replicas}")

        elif queue_len >= self.queue_threshold:
            self.backend_replicas += 1
            decisions.append({
                "action": "horizontal",
                "service": "backend",
                "replicas": self.backend_replicas,
                "reason": f"Queue depth ({queue_len}) crossed limit of {self.queue_threshold}"
            })
            _logger.warning(f"Horizontal scale-up triggered due to queue depth: replicas={self.backend_replicas}")

        # 2. Vertical Scaling Check (Memory allocation increase)
        if mem >= self.mem_threshold:
            old_mem = self.backend_memory_limit_mb
            self.backend_memory_limit_mb += 256
            decisions.append({
                "action": "vertical",
                "service": "backend",
                "memory_limit_mb": self.backend_memory_limit_mb,
                "reason": f"Memory usage ({mem}%) crossed threshold of {self.mem_threshold}%"
            })
            _logger.warning(f"Vertical scale-up triggered: memory limit={self.backend_memory_limit_mb}MB (was {old_mem}MB)")

        # Scale down simulation logic (for cooldown when load drops)
        if cpu < 30.0 and self.backend_replicas > 1:
            self.backend_replicas -= 1
            decisions.append({
                "action": "horizontal",
                "service": "backend",
                "replicas": self.backend_replicas,
                "reason": f"CPU usage is idle ({cpu}%), cooling down scaling replicas"
            })
            _logger.info(f"Horizontal scale-down triggered: replicas={self.backend_replicas}")

        return decisions
