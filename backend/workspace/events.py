"""
AIForge Workspace Event Bus
===========================
Async event-driven agent communication bus.
Allows specialized agents (Planner, Architect, Backend, Frontend, Reviewer, Testing, DevOps)
to publish and subscribe to real-time events:
'Task Started', 'Task Finished', 'Bug Found', 'API Ready', 'Database Complete', 'Frontend Waiting', 'Tests Passed'.
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Callable, Optional

_logger = logging.getLogger("aiforge.workspace")


class WorkspaceEventBus:
    """
    Event Bus for agent collaboration and event broadcasting.
    """

    def __init__(self) -> None:
        self.subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
        self.event_history: List[Dict[str, Any]] = []

    def subscribe(self, event_type: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        _logger.info(f"WorkspaceEventBus: Agent subscribed to event '{event_type}'")

    def publish(self, event_type: str, project_id: str, sender_agent: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        event = {
            "event_type": event_type,
            "project_id": project_id,
            "sender_agent": sender_agent,
            "payload": payload,
            "timestamp": time.time()
        }
        self.event_history.append(event)
        _logger.info(f"WorkspaceEventBus [{event_type}] from '{sender_agent}' in project '{project_id}'")

        if event_type in self.subscribers:
            for cb in self.subscribers[event_type]:
                try:
                    cb(event)
                except Exception as e:
                    _logger.error(f"Error executing callback for event '{event_type}': {e}")

        return event

    def get_project_events(self, project_id: str) -> List[Dict[str, Any]]:
        return [e for e in self.event_history if e.get("project_id") == project_id]

    def get_all_events(self) -> List[Dict[str, Any]]:
        return self.event_history


global_event_bus = WorkspaceEventBus()
