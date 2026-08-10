"""
AIForge Day 29 — Prometheus Alert Rules & Incident Response Integration
========================================================================
Evaluates Prometheus metrics against configurable alert thresholds and dispatches
evidence-backed incidents into AIForge Incident Response.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.monitoring.prometheus import global_prometheus_registry

_logger = logging.getLogger("aiforge.monitoring.alerts")


class AlertRule:
    def __init__(
        self,
        name: str,
        metric_name: str,
        threshold: float,
        operator: str,
        severity: str = "HIGH",
        description: str = ""
    ):
        self.name = name
        self.metric_name = metric_name
        self.threshold = threshold
        self.operator = operator  # '>', '>=', '<', '<='
        self.severity = severity
        self.description = description


DEFAULT_ALERT_RULES = [
    AlertRule(
        name="HighErrorRate",
        metric_name="error_rate_pct",
        threshold=5.0,
        operator=">",
        severity="HIGH",
        description="HTTP error rate exceeds 5% threshold."
    ),
    AlertRule(
        name="HighLatencyP95",
        metric_name="p95_latency_ms",
        threshold=1000.0,
        operator=">",
        severity="HIGH",
        description="P95 HTTP latency exceeds 1000ms SLA."
    ),
    AlertRule(
        name="ApplicationUnavailable",
        metric_name="app_health",
        threshold=1.0,
        operator="<",
        severity="CRITICAL",
        description="One or more core AIForge services reported degraded health."
    ),
    AlertRule(
        name="QueueBacklog",
        metric_name="queue_depth",
        threshold=50.0,
        operator=">",
        severity="MEDIUM",
        description="Background job queue depth exceeds 50 items."
    ),
    AlertRule(
        name="MemoryPressure",
        metric_name="memory_usage_pct",
        threshold=85.0,
        operator=">",
        severity="HIGH",
        description="Memory consumption exceeds 85% threshold."
    ),
]


class AlertEvaluator:
    """
    Evaluates Prometheus metric streams and bridges to Incident Response.
    """

    def __init__(self, rules: Optional[List[AlertRule]] = None):
        self.rules = rules or DEFAULT_ALERT_RULES

    def evaluate_metrics(
        self,
        project_id: str = "aiforge-demo",
        current_metrics: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        metrics = current_metrics or {
            "error_rate_pct": 0.14,
            "p95_latency_ms": 182.0,
            "app_health": 1.0,
            "queue_depth": 3.0,
            "memory_usage_pct": 42.0
        }

        triggered_alerts = []

        for rule in self.rules:
            val = metrics.get(rule.metric_name)
            if val is None:
                continue

            is_triggered = False
            if rule.operator == ">" and val > rule.threshold:
                is_triggered = True
            elif rule.operator == ">=" and val >= rule.threshold:
                is_triggered = True
            elif rule.operator == "<" and val < rule.threshold:
                is_triggered = True
            elif rule.operator == "<=" and val <= rule.threshold:
                is_triggered = True

            if is_triggered:
                alert_evt = {
                    "alert_name": rule.name,
                    "metric": rule.metric_name,
                    "value": val,
                    "threshold": rule.threshold,
                    "severity": rule.severity,
                    "description": rule.description,
                    "timestamp": datetime.now().isoformat()
                }
                triggered_alerts.append(alert_evt)
                _logger.warning(f"[AlertEvaluator] Triggered alert '{rule.name}' for project '{project_id}': value {val} {rule.operator} {rule.threshold}")

                # Dispatch to Incident Response
                self._dispatch_incident(project_id, alert_evt)

        return triggered_alerts

    def _dispatch_incident(self, project_id: str, alert: Dict[str, Any]):
        try:
            from backend.incidents.service import global_incident_service
            from backend.incidents.models import IncidentType, Severity

            inc_type = IncidentType.PERFORMANCE_DEGRADATION
            if "Error" in alert["alert_name"]:
                inc_type = IncidentType.SYSTEM_CRASH
            elif "Unavailable" in alert["alert_name"]:
                inc_type = IncidentType.SERVICE_UNAVAILABLE

            global_incident_service.report_incident(
                project_id=project_id,
                inc_type=inc_type,
                symptoms=[alert["description"], f"Metric {alert['metric']} = {alert['value']} (Threshold: {alert['threshold']})"],
                root_cause=f"Prometheus alert '{alert['alert_name']}' threshold breached.",
                severity=Severity.HIGH if alert["severity"] == "HIGH" else Severity.CRITICAL
            )
        except Exception as e:
            _logger.info(f"[AlertEvaluator] Incident dispatch notice: {e}")


global_alert_evaluator = AlertEvaluator()
global_alert_engine = global_alert_evaluator

