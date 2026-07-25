"""
AIForge V2 – Asynchronous Event Bus Infrastructure
===================================================
Decoupled event publisher-subscriber engine for inter-agent workflows.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Callable, Awaitable

_logger = logging.getLogger("aiforge.v2.events")


class Event:
    def __init__(self, topic: str, payload: Dict[str, Any], sender: str = "system"):
        self.topic = topic
        self.payload = payload
        self.sender = sender
        self.timestamp = time.time()


class EventBus:
    """
    In-Memory & PubSub Asynchronous Event Bus for AIForge V2.
    """

    def __init__(self):
        self._listeners: Dict[str, List[Callable[[Event], Awaitable[None]]]] = {}
        self._history: List[Event] = []

    def subscribe(self, topic: str, listener: Callable[[Event], Awaitable[None]]) -> None:
        if topic not in self._listeners:
            self._listeners[topic] = []
        self._listeners[topic].append(listener)
        _logger.info(f"EventBus: Subscribed listener to topic '{topic}'")

    async def publish(self, topic: str, payload: Dict[str, Any], sender: str = "system") -> Event:
        event = Event(topic=topic, payload=payload, sender=sender)
        self._history.append(event)
        _logger.info(f"EventBus: Published event topic='{topic}' sender='{sender}'")

        if topic in self._listeners:
            for listener in self._listeners[topic]:
                try:
                    await listener(event)
                except Exception as exc:
                    _logger.error(f"EventBus listener error on topic '{topic}': {exc}")

        return event

    def get_history(self, topic: str = None) -> List[Event]:
        if topic:
            return [e for e in self._history if e.topic == topic]
        return list(self._history)


global_event_bus = EventBus()
