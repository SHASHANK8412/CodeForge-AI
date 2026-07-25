"""
AIForge V2 – Event Dispatcher Infrastructure
=============================================
Central dispatcher routing inter-agent messages and events between CEO, Manager, and engineering agents.
"""

import asyncio
import logging
from typing import Dict, Any, List, Callable, Awaitable
from v2.core.message import CoreAgentMessage

_logger = logging.getLogger("aiforge.v2.core.dispatcher")


class EventDispatcher:
    """
    Inter-Agent Message & Event Dispatcher.
    """

    def __init__(self):
        self._routes: Dict[str, List[Callable[[CoreAgentMessage], Awaitable[None]]]] = {}
        self._message_log: List[CoreAgentMessage] = []

    def register_handler(self, receiver: str, handler: Callable[[CoreAgentMessage], Awaitable[None]]) -> None:
        if receiver not in self._routes:
            self._routes[receiver] = []
        self._routes[receiver].append(handler)
        _logger.info(f"EventDispatcher: Registered handler for receiver '{receiver}'")

    async def dispatch(self, message: CoreAgentMessage) -> None:
        self._message_log.append(message)
        _logger.info(f"EventDispatcher: Dispatching message from '{message.sender}' -> '{message.receiver}' (Task: {message.task_id})")

        handlers = self._routes.get(message.receiver, [])
        for handler in handlers:
            try:
                await handler(message)
            except Exception as exc:
                _logger.error(f"EventDispatcher error processing message to '{message.receiver}': {exc}")

    def get_log(self) -> List[CoreAgentMessage]:
        return list(self._message_log)


global_event_dispatcher = EventDispatcher()
