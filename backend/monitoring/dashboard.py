"""
AIForge Operations Dashboard Service (Day 46)
============================================
Aggregates telemetry traces, metrics, system health, active alerts, and model performance into real-time operations dashboard payloads.
"""

import time
import logging
from typing import Dict, Any
from backend.monitoring.metrics import global_metrics_collector
from backend.monitoring.health import global_health_checker
from backend.monitoring.alerts import global_alert_engine
from backend.monitoring.tracing import global_distributed_tracing

_logger = logging.getLogger("aiforge.monitoring.dashboard")


class OperationsDashboardService:
    """
    Service aggregating real-time operational telemetry for frontend UI dashboards.
    """

    def get_operations_dashboard(self) -> Dict[str, Any]:
        metrics = global_metrics_collector.collect_system_metrics()
        health = global_health_checker.check_all_components()
        alerts = global_alert_engine.evaluate_system_alerts(metrics)
        traces_count = len(global_distributed_tracing.traces)

        return {
            "timestamp": time.time(),
            "metrics": metrics,
            "health": health,
            "active_alerts_count": len(alerts),
            "alerts": alerts,
            "total_traces": traces_count,
            "operational_status": "NORMAL" if len(alerts) == 0 else "DEGRADED_AUTONOMOUS_HEALING"
        }


global_operations_dashboard = OperationsDashboardService()
