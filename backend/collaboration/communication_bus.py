"""
Day 43 - Agent Communication Bus
=================================
In-memory event message bus facilitating real-time inter-agent messaging and state sharing.
"""

from typing import List, Dict, Any, Callable
from dataclasses import dataclass, field
import time


@dataclass
class BusMessage:
    sender: str
    topic: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)


class CommunicationBus:
    """Event message bus for broadcasting and querying inter-agent messages."""

    def __init__(self):
        self.message_history: List[BusMessage] = []
        self.subscribers: Dict[str, List[Callable[[BusMessage], None]]] = {}

    def subscribe(self, topic: str, handler: Callable[[BusMessage], None]):
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(handler)

    def publish(self, sender: str, topic: str, payload: Dict[str, Any]) -> BusMessage:
        msg = BusMessage(sender=sender, topic=topic, payload=payload, timestamp=time.time())
        self.message_history.append(msg)

        if topic in self.subscribers:
            for handler in self.subscribers[topic]:
                try:
                    handler(msg)
                except Exception as e:
                    print(f"Error executing subscriber handler for {topic}: {e}")

        return msg

    def get_messages(self, topic: str = None, sender: str = None) -> List[BusMessage]:
        msgs = self.message_history
        if topic:
            msgs = [m for m in msgs if m.topic == topic]
        if sender:
            msgs = [m for m in msgs if m.sender == sender]
        return msgs

    def clear(self):
        self.message_history.clear()
        self.subscribers.clear()
