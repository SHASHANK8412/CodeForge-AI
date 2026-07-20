import time
import logging
from typing import Dict, Any, List
from pydantic import BaseModel

_logger = logging.getLogger("aiforge.sre")

class Incident(BaseModel):
    """
    Represents an active operational incident in the system.
    """
    incident_id: str
    signature: str
    severity: str  # Info, Warning, Critical, Emergency
    description: str
    timestamp: float
    service: str
    status: str = "Active"

class IncidentDetector:
    """
    Scans metrics snapshots and health check indicators to detect threshold violations and downtime events.
    """

    def __init__(self) -> None:
        pass

    def detect_incidents(self, metrics: Dict[str, Any], health: Dict[str, Any]) -> List[Incident]:
        """
        Processes current telemetry and health status to extract active incidents.
        """
        incidents: List[Incident] = []
        timestamp = time.time()

        infra = metrics.get("infrastructure", {})
        apps = metrics.get("application", {})
        checks = health.get("checks", {})

        # 1. Host CPU check
        cpu = infra.get("cpu_utilization", 0.0)
        if cpu >= 90.0:
            incidents.append(Incident(
                incident_id=f"cpu_{int(timestamp)}",
                signature="high_cpu",
                severity="Critical",
                description=f"Host CPU saturation detected at {cpu}%",
                timestamp=timestamp,
                service="Host Infrastructure"
            ))
        elif cpu >= 75.0:
            incidents.append(Incident(
                incident_id=f"cpu_{int(timestamp)}",
                signature="high_cpu",
                severity="Warning",
                description=f"Host CPU warning at {cpu}%",
                timestamp=timestamp,
                service="Host Infrastructure"
            ))

        # 2. Host Memory check
        mem = infra.get("memory_utilization", 0.0)
        if mem >= 90.0:
            incidents.append(Incident(
                incident_id=f"mem_{int(timestamp)}",
                signature="memory_leak",
                severity="Critical",
                description=f"Host Memory saturation detected at {mem}%",
                timestamp=timestamp,
                service="Host Infrastructure"
            ))

        # 3. Disk usage check
        disk = infra.get("disk_utilization", 0.0)
        if disk >= 95.0:
            incidents.append(Incident(
                incident_id=f"disk_{int(timestamp)}",
                signature="disk_exhaustion",
                severity="Critical",
                description=f"Host Disk capacity critical at {disk}%",
                timestamp=timestamp,
                service="Host Infrastructure"
            ))

        # 4. API check
        api_chk = checks.get("api", {})
        if api_chk.get("status") == "Unhealthy":
            incidents.append(Incident(
                incident_id=f"api_{int(timestamp)}",
                signature="api_downtime",
                severity="Emergency",
                description=f"FastAPI Backend API is down. Error: {api_chk.get('error')}",
                timestamp=timestamp,
                service="Backend API"
            ))

        # 5. Database check
        db_chk = checks.get("database", {})
        if db_chk.get("status") == "Unhealthy":
            incidents.append(Incident(
                incident_id=f"db_{int(timestamp)}",
                signature="db_connection_failure",
                severity="Critical",
                description="Failed to establish PostgreSQL database connection handle.",
                timestamp=timestamp,
                service="Database Engine"
            ))

        # 6. Redis check
        redis_chk = checks.get("redis", {})
        if redis_chk.get("status") == "Unhealthy":
            incidents.append(Incident(
                incident_id=f"redis_{int(timestamp)}",
                signature="redis_failure",
                severity="Warning",
                description="Redis cache engine connection timed out.",
                timestamp=timestamp,
                service="Cache Service"
            ))

        # 7. Latency check
        resp_time = apps.get("response_time_ms", 0.0)
        if resp_time >= 3000.0:
            incidents.append(Incident(
                incident_id=f"latency_{int(timestamp)}",
                signature="slow_responses",
                severity="Warning",
                description=f"Response time degradation: avg latency is {resp_time:.1f}ms",
                timestamp=timestamp,
                service="Backend API"
            ))

        # 8. Error rate check
        err_rate = apps.get("error_rate_pct", 0.0)
        if err_rate >= 15.0:
            incidents.append(Incident(
                incident_id=f"error_{int(timestamp)}",
                signature="high_error_rate",
                severity="Critical",
                description=f"High HTTP API error rate: {err_rate:.1f}% errors",
                timestamp=timestamp,
                service="Backend API"
            ))

        # 9. Ollama outage check
        ollama_chk = checks.get("ollama", {})
        if ollama_chk.get("status") == "Unhealthy":
            incidents.append(Incident(
                incident_id=f"ollama_{int(timestamp)}",
                signature="ollama_failure",
                severity="Critical",
                description=f"Ollama local LLM API offline: {ollama_chk.get('error')}",
                timestamp=timestamp,
                service="LLM Inference Host"
            ))

        return incidents
