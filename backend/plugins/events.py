import logging
from typing import Dict, Any, List, Callable

_logger = logging.getLogger("aiforge.plugins")

class PluginEventBus:
    """
    Subscribes to and broadcasts plugin lifecycle change notifications.
    """

    def __init__(self) -> None:
        self.subscribers: Dict[str, List[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: str, callback: Callable[[Any], None]) -> None:
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def publish(self, event_type: str, data: Any) -> None:
        _logger.info(f"Broadcasting plugin event: '{event_type}'")
        callbacks = self.subscribers.get(event_type, [])
        for cb in callbacks:
            try:
                cb(data)
            except Exception as e:
                _logger.error(f"Error executing SRE plugin event callback: {str(e)}")
