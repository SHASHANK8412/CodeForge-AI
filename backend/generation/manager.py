"""
backend/generation/manager.py
==============================
Orchestrates the LangGraph parallel_graph pipeline for a given generation.

Key responsibilities
---------------------
1. Creates/updates generation records via GenerationStore.
2. Opens a live SSE channel via GenerationEventBus.
3. Injects a ContextVar callback into each node so that lifecycle
   events (started/completed/failed) are captured without modifying
   any agent logic.
4. Runs parallel_graph.ainvoke() in a background asyncio.Task.
5. Handles cancellation cleanly.
6. Persists final project files and quality results after completion.

Thread model
------------
Each generation runs in one asyncio.Task (not a thread).
The ContextVar `generation_event_callback_var` is set on the Task's
context so it is visible to every node that runs inside that task,
including the parallel fan-out branches.
"""

from __future__ import annotations

import asyncio
import logging
from time import perf_counter
from typing import Dict, Optional

from backend.generation.store import global_generation_store as _store
from backend.generation.event_bus import global_event_bus as _bus
from backend.graph.parallel_workflow import (
    parallel_graph,
    generation_event_callback_var,
)
from backend.graph.project_state import ProjectState

_logger = logging.getLogger("aiforge.generation.manager")

# ---------------------------------------------------------------------------
# Per-generation active asyncio.Task registry (in-process only)
# ---------------------------------------------------------------------------
_active_tasks: Dict[str, asyncio.Task] = {}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_callback(gen_id: str):
    """
    Returns a synchronous callback that the parallel_workflow nodes invoke
    at key lifecycle points. The callback updates both the store and the bus.
    """
    def _cb(event_type: str, agent_name: str, *, duration: float = 0.0, error: str = "") -> None:
        try:
            # --- Store update ---
            if event_type == "agent_started":
                _store.agent_started(gen_id, agent_name)
                _store.add_event(gen_id, "agent_started", agent=agent_name,
                                 message=f"{agent_name.title()} started")
            elif event_type == "agent_completed":
                _store.agent_completed(gen_id, agent_name, duration=duration)
                progress = _store.get(gen_id, {}).get("progress", 0)
                _store.add_event(gen_id, "agent_completed", agent=agent_name,
                                 message=f"{agent_name.title()} completed in {duration:.1f}s",
                                 metadata={"duration": round(duration, 3)})
            elif event_type == "agent_failed":
                _store.agent_failed(gen_id, agent_name, error=error)
                _store.add_event(gen_id, "agent_failed", agent=agent_name,
                                 message=f"{agent_name.title()} failed",
                                 metadata={"safe_error": error[:200] if error else ""})
            elif event_type == "agent_retrying":
                _store.agent_retrying(gen_id, agent_name)
                _store.add_event(gen_id, "agent_retrying", agent=agent_name,
                                 message=f"{agent_name.title()} retrying")

            # --- Bus emit (non-blocking) ---
            progress = _store.get(gen_id, {}).get("progress", 0)
            _bus.emit_sync(
                gen_id, event_type,
                agent=agent_name,
                message=f"{agent_name.title()} {event_type.replace('agent_', '')}",
                metadata={"duration": round(duration, 3)} if duration else {},
                progress=progress,
            )
        except Exception as exc:  # noqa: BLE001
            _logger.warning("Lifecycle callback error for %s/%s: %s", gen_id, agent_name, exc)

    return _cb


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class GenerationManager:
    """
    Creates and runs project generations against the parallel_graph.
    """

    def create(
        self,
        project_id: str,
        user_id: str,
        prompt: str,
    ) -> str:
        """
        Persist a new generation record and return the generation_id.
        Does NOT start execution — call run() next.
        """
        gen_id = _store.create(project_id, user_id, prompt)
        _store.add_event(gen_id, "generation_queued", message="Generation queued")
        return gen_id

    async def run(self, gen_id: str) -> None:
        """
        Start the LangGraph parallel_graph for gen_id as a background asyncio.Task.
        Returns immediately — the browser observes progress via SSE or polling.
        """
        rec = _store.get(gen_id)
        if not rec:
            _logger.error("GenerationManager.run called with unknown gen_id=%s", gen_id)
            return

        # Open the SSE channel
        _bus.open(gen_id)
        _store.update_status(gen_id, "planning")
        _store.add_event(gen_id, "generation_started", message="Generation started")
        await _bus.emit(gen_id, "generation_started", message="Generation started")

        task = asyncio.create_task(
            self._run_pipeline(gen_id, rec),
            name=f"aiforge-gen-{gen_id}",
        )
        _active_tasks[gen_id] = task
        task.add_done_callback(lambda t: _active_tasks.pop(gen_id, None))

    async def _run_pipeline(self, gen_id: str, rec: dict) -> None:
        """Background task: runs parallel_graph.ainvoke() with lifecycle hooks."""
        prompt = rec.get("prompt", "")
        project_name = rec.get("project_id", "AIForgeApp")
        user_id = rec.get("user_id", "default")

        cb = _make_callback(gen_id)

        initial_state: ProjectState = {
            "user_request": prompt,
            "user_prompt": prompt,
            "prompt": prompt,
            "project_name": project_name,
            "session_id": gen_id,
            "requirements": [prompt],
            "files": {},
            "dependencies": {},
            "commands": {},
            "execution_results": {},
            "test_results": {},
            "errors": [],
            "fixes": [],
            "iteration": 0,
            "max_iterations": 3,
            "status": "NOT_STARTED",
            "stream_events": [],
        }

        # Inject the callback ContextVar into this task's context
        token = generation_event_callback_var.set(cb)
        started_at = perf_counter()

        try:
            _logger.info("[GENERATION] %s pipeline started", gen_id)
            final_state = await parallel_graph.ainvoke(initial_state)

            elapsed = perf_counter() - started_at
            _logger.info("[GENERATION] %s completed in %.1fs", gen_id, elapsed)

            # Persist any final file paths from the state
            project_path = final_state.get("project_path", "")
            _store.update_status(gen_id, "completed")
            _store.add_event(
                gen_id, "generation_completed",
                message="Generation completed successfully",
                metadata={
                    "duration": round(elapsed, 2),
                    "project_path": project_path,
                    "files_count": len(final_state.get("files", {})),
                }
            )
            await _bus.emit(
                gen_id, "generation_completed",
                message="Generation completed successfully",
                metadata={
                    "duration": round(elapsed, 2),
                    "project_path": project_path,
                },
                progress=100,
            )

        except asyncio.CancelledError:
            _logger.info("[GENERATION] %s cancelled", gen_id)
            _store.update_status(gen_id, "cancelled")
            _store.add_event(gen_id, "generation_cancelled", message="Generation cancelled by user")
            await _bus.emit(gen_id, "generation_cancelled", message="Generation cancelled")

        except Exception as exc:  # noqa: BLE001
            elapsed = perf_counter() - started_at
            safe_msg = f"Generation failed after {elapsed:.1f}s. Please try again."
            _logger.error("[GENERATION] %s failed: %s", gen_id, exc)
            _store.update_status(gen_id, "failed", error=safe_msg)
            _store.add_event(
                gen_id, "generation_failed",
                message=safe_msg,
                metadata={"duration": round(elapsed, 2)}
            )
            await _bus.emit(
                gen_id, "generation_failed",
                message=safe_msg,
                metadata={"duration": round(elapsed, 2)},
            )

        finally:
            generation_event_callback_var.reset(token)
            # Give subscribers a moment to receive the final event then close
            await asyncio.sleep(0.2)
            _bus.close(gen_id)

    async def cancel(self, gen_id: str) -> bool:
        """Cancel a running generation. Returns True if it was active."""
        task = _active_tasks.get(gen_id)
        if task and not task.done():
            task.cancel()
            _store.update_status(gen_id, "cancelled")
            _logger.info("[GENERATION] %s cancel requested", gen_id)
            return True
        return False

    def is_active(self, gen_id: str) -> bool:
        task = _active_tasks.get(gen_id)
        return task is not None and not task.done()


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
global_generation_manager = GenerationManager()
