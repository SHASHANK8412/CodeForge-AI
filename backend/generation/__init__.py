"""
AIForge Generation Engine
=========================
Persistent, real-time observable generation lifecycle layer.

Modules:
  store   — JSON-backed persistent generation + event records
  event_bus — per-generation asyncio.Queue for SSE streaming
  manager  — orchestrates parallel_graph.ainvoke() with lifecycle hooks
  routes   — FastAPI REST + SSE endpoints
"""
