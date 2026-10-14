"""
backend/generation/event_bus.py
================================
Per-generation asyncio.Queue for real-time SSE streaming.

Each active generation gets its own queue. The GenerationManager writes
events to the queue; the SSE endpoint reads and streams them to the browser.

The bus is purely in-process — it's not persisted (persistence is handled by
GenerationStore). On reconnect the frontend calls GET /api/generations/{id}
first to restore state, then reattaches to the live SSE stream.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Optional

_logger = logging.getLogger("aiforge.generation.event_bus")

# Sentinel value used to signal that an SSE stream should close
_STREAM_DONE = "__STREAM_DONE__"

# Max events to buffer per generation before the oldest are dropped
_QUEUE_MAX = 512


class GenerationEventBus:
    """
    In-process asyncio event bus for broadcasting generation events to SSE clients.

    Usage
    -----
    bus = GenerationEventBus()
    bus.open(gen_id)          # called when generation starts
    await bus.emit(gen_id, "agent_started", agent="planner", message="Planner started")
    async for sse_line in bus.subscribe(gen_id):
        yield sse_line        # each sse_line is a formatted SSE string
    bus.close(gen_id)         # called when generation ends
    """

    def __init__(self) -> None:
        # gen_id -> asyncio.Queue[dict | str]
        self._queues: Dict[str, asyncio.Queue] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def open(self, gen_id: str) -> None:
        """Open a queue for a new generation."""
        if gen_id not in self._queues:
            self._queues[gen_id] = asyncio.Queue(maxsize=_QUEUE_MAX)
        _logger.debug("EventBus opened for %s", gen_id)

    def close(self, gen_id: str) -> None:
        """Signal SSE subscribers to close and remove the queue."""
        q = self._queues.get(gen_id)
        if q:
            try:
                q.put_nowait(_STREAM_DONE)
            except asyncio.QueueFull:
                pass
        _logger.debug("EventBus closed for %s", gen_id)

    # ------------------------------------------------------------------
    # Emit (write side — called from GenerationManager background task)
    # ------------------------------------------------------------------

    async def emit(
        self,
        gen_id: str,
        event_type: str,
        *,
        agent: Optional[str] = None,
        message: str = "",
        metadata: Optional[dict] = None,
        progress: Optional[int] = None,
    ) -> None:
        """Put an event onto the queue. Non-blocking if queue is full (drops oldest)."""
        q = self._queues.get(gen_id)
        if not q:
            return
        payload: dict = {
            "type": event_type,
            "agent": agent,
            "message": message,
            "metadata": metadata or {},
        }
        if progress is not None:
            payload["progress"] = progress
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            # Drop oldest to make room
            try:
                q.get_nowait()
            except asyncio.QueueEmpty:
                pass
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                _logger.warning("EventBus queue full, event dropped for %s", gen_id)

    def emit_sync(
        self,
        gen_id: str,
        event_type: str,
        *,
        agent: Optional[str] = None,
        message: str = "",
        metadata: Optional[dict] = None,
        progress: Optional[int] = None,
    ) -> None:
        """Thread-safe emit from synchronous code (e.g., non-async callbacks)."""
        q = self._queues.get(gen_id)
        if not q:
            return
        payload: dict = {
            "type": event_type,
            "agent": agent,
            "message": message,
            "metadata": metadata or {},
        }
        if progress is not None:
            payload["progress"] = progress
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            _logger.warning("EventBus sync queue full for %s", gen_id)

    # ------------------------------------------------------------------
    # Subscribe (read side — consumed by SSE endpoint)
    # ------------------------------------------------------------------

    async def subscribe(self, gen_id: str) -> AsyncGenerator[str, None]:
        """
        Async generator that yields formatted SSE lines.

        Each yielded string is a complete SSE message, e.g.:
            'event: agent_started\ndata: {"agent":"planner"}\n\n'
        """
        q = self._queues.get(gen_id)
        if not q:
            # Generation already completed or unknown; yield nothing
            return

        while True:
            try:
                item = await asyncio.wait_for(q.get(), timeout=25.0)
            except asyncio.TimeoutError:
                # Keep-alive heartbeat so the connection stays open
                yield "event: heartbeat\ndata: {}\n\n"
                continue

            if item == _STREAM_DONE:
                yield "event: stream_done\ndata: {}\n\n"
                return

            event_type = item.get("type", "event")
            data = json.dumps(item)
            yield f"event: {event_type}\ndata: {data}\n\n"

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def is_active(self, gen_id: str) -> bool:
        return gen_id in self._queues


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
global_event_bus = GenerationEventBus()
