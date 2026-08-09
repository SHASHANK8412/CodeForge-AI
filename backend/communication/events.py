"""
AIForge Event System & Dispatcher
=================================
Provides event publishing, agent subscriptions, and event timeline tracking across the autonomous software engineering workflow.
"""

import time
import logging
from typing import Dict, Any, List, Callable, Optional

_logger = logging.getLogger("aiforge.communication.events")


class SystemEventType:
    PROJECT_STARTED = "PROJECT_STARTED"
    TASK_ASSIGNED = "TASK_ASSIGNED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"
    AGENT_RETRY = "AGENT_RETRY"
    BUILD_FINISHED = "BUILD_FINISHED"
    DEPLOYMENT_STARTED = "DEPLOYMENT_STARTED"
    DEPLOYMENT_COMPLETED = "DEPLOYMENT_COMPLETED"

    ALL_EVENTS = [
        PROJECT_STARTED, TASK_ASSIGNED, TASK_COMPLETED, TASK_FAILED,
        AGENT_RETRY, BUILD_FINISHED, DEPLOYMENT_STARTED, DEPLOYMENT_COMPLETED
    ]


class EventDispatcher:
    """
    Publish/Subscribe event system for agents.
    """

    def __init__(self) -> None:
        self.subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
        self.event_history: List[Dict[str, Any]] = [
            {
                "event_id": "event_001",
                "event_type": SystemEventType.PROJECT_STARTED,
                "publisher": "Project Manager",
                "data": {"project_name": "Food Delivery App"},
                "timestamp": time.time() - 3600
            },
            {
                "event_id": "event_002",
                "event_type": SystemEventType.TASK_ASSIGNED,
                "publisher": "Project Manager",
                "data": {"agent": "Architect Agent", "task": "Design System Architecture"},
                "timestamp": time.time() - 3500
            }
        ]

    def subscribe(self, event_type: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        _logger.info(f"EventDispatcher: Subscribed callback to '{event_type}'")

    def publish(self, event_type: str, publisher: str, data: Dict[str, Any]) -> Dict[str, Any]:
        event_obj = {
            "event_id": f"event_{int(time.time() * 1000)}",
            "event_type": event_type,
            "publisher": publisher,
            "data": data,
            "timestamp": time.time()
        }
        self.event_history.append(event_obj)
        _logger.info(f"EventDispatcher: [{event_type}] Published by '{publisher}'")

        # Notify subscribers
        if event_type in self.subscribers:
            for cb in self.subscribers[event_type]:
                try:
                    cb(event_obj)
                except Exception as e:
                    _logger.error(f"Error executing subscriber for event '{event_type}': {e}")

        return event_obj

    def get_event_timeline(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.event_history[-limit:]


global_event_dispatcher = EventDispatcher()
