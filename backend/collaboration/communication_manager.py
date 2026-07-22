"""
Production-Grade Multi-Agent Communication Manager for AIForge
===============================================================
Comprehensive Communication Infrastructure supporting:
1. Structured Message Protocol (Pydantic / Dataclass with trace & context propagation)
2. Thread-Safe & Async-Safe Shared Memory Workspace with Atomic Locks
3. Event-Driven Pub/Sub Broker
4. Priority Task Queue & Dead-Letter Queue (DLQ)
5. Exponential Backoff Retry Engine
6. Agent Heartbeat & Health Monitoring (HEALTHY, DEGRADED, UNHEALTHY, DEAD)
7. Full Support for all 9 Agent Types:
   [Planner, Architect, Frontend, Backend, Database, Reviewer, Testing, Documentation, Deployment]
"""

import asyncio
import time
import uuid
import copy
import logging
import threading
from enum import Enum
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field

_logger = logging.getLogger("aiforge.communication_manager")
_logger.setLevel(logging.INFO)


class AgentRole(str, Enum):
    PLANNER = "Planner"
    ARCHITECT = "Architect"
    FRONTEND = "Frontend"
    BACKEND = "Backend"
    DATABASE = "Database"
    REVIEWER = "Reviewer"
    TESTING = "Testing"
    DOCUMENTATION = "Documentation"
    DEPLOYMENT = "Deployment"


class AgentHealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    DEAD = "DEAD"


class MessagePriority(int, Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentMessage:
    """Structured Message Protocol with trace & context propagation."""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    recipient: str = "ALL"  # Specific agent name or 'ALL'
    topic: str = "general"
    payload: Dict[str, Any] = field(default_factory=dict)
    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class AgentHeartbeat:
    """Agent vitality metrics."""
    agent_name: str
    role: AgentRole
    last_heartbeat: float = field(default_factory=time.time)
    status: AgentHealthStatus = AgentHealthStatus.HEALTHY
    processed_messages: int = 0
    failed_messages: int = 0
    cpu_percent: float = 0.0
    memory_mb: float = 0.0


class ThreadSafeSharedMemoryWorkspace:
    """Thread-safe & Async-safe central memory workspace with atomic locking."""

    def __init__(self):
        self._lock = threading.RLock()
        self._store: Dict[str, Any] = {
            "metadata": {"system": "AIForge", "version": "2.0.0"},
            "registries": {
                "api": [],
                "db_schema": [],
                "components": [],
                "docs": []
            },
            "artifacts": {}
        }

    def set(self, key: str, value: Any):
        with self._lock:
            self._store[key] = copy.deepcopy(value)

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            val = self._store.get(key, default)
            return copy.deepcopy(val) if val is not None else default

    def update_registry(self, registry_name: str, item: Any):
        with self._lock:
            if "registries" not in self._store:
                self._store["registries"] = {}
            if registry_name not in self._store["registries"]:
                self._store["registries"][registry_name] = []
            self._store["registries"][registry_name].append(copy.deepcopy(item))

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._store)


class EventBroker:
    """Event-driven pub/sub communication system."""

    def __init__(self):
        self._lock = threading.RLock()
        self._subscriptions: Dict[str, List[Callable[[AgentMessage], None]]] = {}
        self._message_history: List[AgentMessage] = []

    def subscribe(self, topic: str, handler: Callable[[AgentMessage], None]):
        with self._lock:
            if topic not in self._subscriptions:
                self._subscriptions[topic] = []
            self._subscriptions[topic].append(handler)

    def publish(self, message: AgentMessage):
        with self._lock:
            self._message_history.append(message)
            handlers = self._subscriptions.get(message.topic, []) + self._subscriptions.get("*", [])

        _logger.info(f"[PUB/SUB] Topic: '{message.topic}' | Sender: {message.sender} -> Recipient: {message.recipient}")

        for h in handlers:
            try:
                h(message)
            except Exception as e:
                _logger.error(f"Error handling message on topic {message.topic}: {e}")

    def get_history(self, topic: Optional[str] = None) -> List[AgentMessage]:
        with self._lock:
            if topic:
                return [m for m in self._message_history if m.topic == topic]
            return list(self._message_history)


class PriorityTaskQueue:
    """Priority task queue with Dead-Letter Queue (DLQ) support."""

    def __init__(self):
        self._queue: List[AgentMessage] = []
        self._dlq: List[AgentMessage] = []
        self._lock = threading.RLock()

    def enqueue(self, message: AgentMessage):
        with self._lock:
            self._queue.append(message)
            # Sort by priority descending (CRITICAL -> LOW), then timestamp ascending
            self._queue.sort(key=lambda m: (-int(m.priority), m.timestamp))

    def dequeue(self) -> Optional[AgentMessage]:
        with self._lock:
            if self._queue:
                return self._queue.pop(0)
            return None

    def send_to_dlq(self, message: AgentMessage, reason: str):
        with self._lock:
            message.payload["dlq_reason"] = reason
            self._dlq.append(message)
            _logger.warning(f"[DLQ] Message {message.message_id} moved to Dead Letter Queue: {reason}")

    def get_dlq(self) -> List[AgentMessage]:
        with self._lock:
            return list(self._dlq)


class HealthMonitor:
    """Monitors agent pings and detects unhealthy or dead workers."""

    def __init__(self, timeout_sec: float = 10.0):
        self._lock = threading.RLock()
        self.timeout_sec = timeout_sec
        self.heartbeats: Dict[str, AgentHeartbeat] = {}

    def register_agent(self, agent_name: str, role: AgentRole):
        with self._lock:
            self.heartbeats[agent_name] = AgentHeartbeat(agent_name=agent_name, role=role)

    def ping(self, agent_name: str, cpu: float = 0.0, mem_mb: float = 0.0):
        with self._lock:
            if agent_name in self.heartbeats:
                hb = self.heartbeats[agent_name]
                hb.last_heartbeat = time.time()
                hb.status = AgentHealthStatus.HEALTHY
                hb.cpu_percent = cpu
                hb.memory_mb = mem_mb

    def record_failure(self, agent_name: str):
        with self._lock:
            if agent_name in self.heartbeats:
                hb = self.heartbeats[agent_name]
                hb.failed_messages += 1
                if hb.failed_messages >= 3:
                    hb.status = AgentHealthStatus.DEGRADED

    def scan_health(self) -> Dict[str, AgentHealthStatus]:
        now = time.time()
        statuses = {}
        with self._lock:
            for name, hb in self.heartbeats.items():
                if now - hb.last_heartbeat > self.timeout_sec * 2:
                    hb.status = AgentHealthStatus.DEAD
                elif now - hb.last_heartbeat > self.timeout_sec:
                    hb.status = AgentHealthStatus.UNHEALTHY
                statuses[name] = hb.status
        return statuses


class CommunicationManager:
    """Master Multi-Agent Communication Manager System."""

    def __init__(self):
        self.shared_memory = ThreadSafeSharedMemoryWorkspace()
        self.event_broker = EventBroker()
        self.task_queue = PriorityTaskQueue()
        self.health_monitor = HealthMonitor()

        # Register all 9 required agents
        all_roles = [
            (AgentRole.PLANNER.value, AgentRole.PLANNER),
            (AgentRole.ARCHITECT.value, AgentRole.ARCHITECT),
            (AgentRole.FRONTEND.value, AgentRole.FRONTEND),
            (AgentRole.BACKEND.value, AgentRole.BACKEND),
            (AgentRole.DATABASE.value, AgentRole.DATABASE),
            (AgentRole.REVIEWER.value, AgentRole.REVIEWER),
            (AgentRole.TESTING.value, AgentRole.TESTING),
            (AgentRole.DOCUMENTATION.value, AgentRole.DOCUMENTATION),
            (AgentRole.DEPLOYMENT.value, AgentRole.DEPLOYMENT),
        ]
        for name, role in all_roles:
            self.health_monitor.register_agent(name, role)

    def send_message(self, sender: str, recipient: str, topic: str, payload: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL) -> AgentMessage:
        msg = AgentMessage(
            sender=sender,
            recipient=recipient,
            topic=topic,
            payload=payload,
            priority=priority
        )
        self.task_queue.enqueue(msg)
        self.event_broker.publish(msg)
        self.health_monitor.ping(sender)
        return msg

    async def process_messages_with_retry(self, handler_func: Callable[[AgentMessage], Any]) -> List[Any]:
        """Processes enqueued messages with exponential backoff retries and failure recovery."""
        results = []

        while True:
            msg = self.task_queue.dequeue()
            if not msg:
                break

            success = False
            for attempt in range(1, msg.max_retries + 1):
                try:
                    res = handler_func(msg)
                    if asyncio.iscoroutine(res):
                        res = await res
                    results.append(res)
                    self.health_monitor.ping(msg.recipient if msg.recipient != "ALL" else msg.sender)
                    success = True
                    break

                except Exception as e:
                    msg.retry_count += 1
                    _logger.warning(f"Attempt {attempt}/{msg.max_retries} failed for message {msg.message_id}: {e}")
                    self.health_monitor.record_failure(msg.sender)

                    if attempt < msg.max_retries:
                        backoff = 0.05 * (2 ** attempt)
                        await asyncio.sleep(backoff)

            if not success:
                self.task_queue.send_to_dlq(msg, f"Exceeded max retries ({msg.max_retries})")

        return results

    def get_system_health(self) -> Dict[str, Any]:
        """Returns complete system health, agent statuses, and DLQ metrics."""
        scan = self.health_monitor.scan_health()
        return {
            "total_agents": len(self.health_monitor.heartbeats),
            "agent_statuses": {name: hb.status.value for name, hb in self.health_monitor.heartbeats.items()},
            "dlq_count": len(self.task_queue.get_dlq()),
            "total_messages_logged": len(self.event_broker.get_history())
        }
