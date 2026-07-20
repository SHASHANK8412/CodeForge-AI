import time
import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.sre")

class AlertManager:
    """
    Formulates and dispatches operational SRE alerts (Slack, Teams, Discord, Emails, Webhooks)
    reporting incident signatures, severities, affected hosts, and healing success statuses.
    """

    def __init__(self, active_channels: List[str] = None) -> None:
        self.active_channels = active_channels or ["slack", "email"]
        self.alerts_sent: List[Dict[str, Any]] = []

    def dispatch_alert(
        self,
        incident_signature: str,
        severity: str,
        affected_service: str,
        details: str,
        recovery_status: str = "Active",
        mttr_seconds: float = None
    ) -> Dict[str, Any]:
        """
        Builds and mock-transmits SRE alert payload to configured notification channels.
        """
        alert_payload = {
            "timestamp": time.time(),
            "incident": incident_signature,
            "severity": severity,
            "service": affected_service,
            "details": details,
            "status": recovery_status,
            "mttr_seconds": mttr_seconds,
        }

        self.alerts_sent.append(alert_payload)

        # Mock dispatch notifications log output
        for channel in self.active_channels:
            chan_lower = channel.lower()
            if chan_lower == "slack":
                _logger.info(f"[ALERT: SLACK] DISPATCHED -> Incident: {incident_signature} | Severity: {severity} | Service: {affected_service} | Status: {recovery_status}")
            elif chan_lower == "discord":
                _logger.info(f"[ALERT: DISCORD] DISPATCHED -> Service: {affected_service} under {severity} load alert.")
            elif chan_lower == "teams":
                _logger.info(f"[ALERT: TEAMS] DISPATCHED -> MS Teams Webhook posted for incident '{incident_signature}'")
            elif chan_lower == "email":
                _logger.info(f"[ALERT: EMAIL] DISPATCHED -> Sending SMTP email to SRE On-Call roster regarding {affected_service} outage.")

        return alert_payload

    def get_alerts_history(self) -> List[Dict[str, Any]]:
        return self.alerts_sent
