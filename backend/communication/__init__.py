"""
AIForge Communication Package
=============================
Agent Communication Bus, Protocol, Shared Project Context, Dependency Manager, Event Dispatcher, Conflict Resolver, and Logging.
"""

from backend.communication.protocol import AgentMessage, MessageType, MessagePriority
from backend.communication.message_bus import global_message_bus, MessageBus
from backend.communication.shared_context import global_shared_context, SharedProjectContext
from backend.communication.events import global_event_dispatcher, EventDispatcher, SystemEventType
from backend.communication.dependency_manager import global_dependency_manager, DependencyManager
from backend.communication.conflict_resolution import global_conflict_resolver, ConflictResolver
from backend.communication.communication_logger import global_communication_logger, CommunicationLogger

__all__ = [
    "AgentMessage", "MessageType", "MessagePriority",
    "global_message_bus", "MessageBus",
    "global_shared_context", "SharedProjectContext",
    "global_event_dispatcher", "EventDispatcher", "SystemEventType",
    "global_dependency_manager", "DependencyManager",
    "global_conflict_resolver", "ConflictResolver",
    "global_communication_logger", "CommunicationLogger"
]
