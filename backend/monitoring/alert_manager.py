import time
import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.sre")


class AlertManager:
    """
    Records operational SRE alerts (incident signature, severity, service, recovery status).
    No notification integration (Slack, Teams, Discord, email, webhooks) is implemented, so alerts are
    recorded and logged only; each record says so in "delivery" instead of claiming it was sent.
    """

    def __init__(self, active_channels: List[str] = None) -> None:
        self.active_channels = active_channels or []      # configured names; none of them is connected
        self.alerts_sent: List[Dict[str, Any]] = []        # kept for compatibility: records, not deliveries

    def dispatch_alert(
        self,
        incident_signature: str,
        severity: str,
        affected_service: str,
        details: str,
        recovery_status: str = "Active",
        mttr_seconds: float = None
    ) -> Dict[str, Any]:
        alert_payload = {
            "timestamp": time.time(),
            "incident": incident_signature,
            "severity": severity,
            "service": affected_service,
            "details": details,
            "status": recovery_status,
            "mttr_seconds": mttr_seconds,
            "delivery": "recorded only: no notification channel is connected"
                        + (f" (configured but not implemented: {', '.join(self.active_channels)})" if self.active_channels else ""),
        }
        self.alerts_sent.append(alert_payload)
        _logger.info("[ALERT recorded, not sent] %s | %s | %s | %s", incident_signature, severity, affected_service, recovery_status)
        return alert_payload

    def get_alerts_history(self) -> List[Dict[str, Any]]:
        return self.alerts_sent
