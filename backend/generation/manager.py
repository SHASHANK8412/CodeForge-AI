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
from backend.memory.codebase_indexer import global_codebase_indexer
from backend.memory.dependency_graph import global_dependency_graph
from backend.memory.project_memory_service import global_project_memory_service
from backend.quality.version_manager import global_version_manager

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

    async def _run_pipeline(self, gen_id: str, rec: dict, is_resume: bool = False) -> None:
        """Background task: runs parallel_graph.ainvoke() with lifecycle hooks and HITL pause detection."""
        prompt = rec.get("prompt", "")
        project_name = rec.get("project_id", "AIForgeApp")
        user_id = rec.get("user_id", "default")

        cb = _make_callback(gen_id)

        config = {"configurable": {"thread_id": gen_id}}

        # Restore existing project files and index if modifying an existing project
        latest_ver = global_version_manager.get_latest_version(project_name)
        existing_files: Dict[str, str] = dict(latest_ver.files_snapshot) if latest_ver else {}

        if existing_files:
            global_codebase_indexer.index_project_files(project_name, existing_files)
            proj_idx = global_codebase_indexer.get_project_index(project_name)
            global_dependency_graph.build_graph_from_index(project_name, proj_idx)
            _logger.info(f"[GENERATION] Loaded {len(existing_files)} existing files for project '{project_name}'")

        initial_state: ProjectState = {
            "project_id": project_name,
            "generation_id": gen_id,
            "user_request": prompt,
            "user_prompt": prompt,
            "prompt": prompt,
            "project_name": project_name,
            "session_id": gen_id,
            "requirements": [prompt],
            "files": existing_files,
            "dependencies": [],
            "commands": [],
            "execution_results": {},
            "test_results": {},
            "errors": [],
            "fixes": [],
            "iteration": 0,
            "max_iterations": 3,
            "status": "RUNNING",
            "approval_status": "pending",
            "approval_required": False,
            "stream_events": [],
        }

        token = generation_event_callback_var.set(cb)
        started_at = perf_counter()

        try:
            _logger.info("[GENERATION] %s pipeline %s", gen_id, "resumed" if is_resume else "started")
            if is_resume:
                final_state = await parallel_graph.ainvoke(None, config=config)
            else:
                final_state = await parallel_graph.ainvoke(initial_state, config=config)

            # Check if workflow is paused at a HITL approval checkpoint
            state_tuple = parallel_graph.get_state(config)
            next_nodes = state_tuple.next if state_tuple else ()

            if next_nodes and any(n in ("human_approval", "final_approval") for n in next_nodes):
                # Paused at approval checkpoint
                current_values = state_tuple.values or {}
                approval_req = current_values.get("approval_request") or {}
                stage = current_values.get("approval_stage") or ("final" if "final_approval" in next_nodes else "architecture")

                _logger.info("[GENERATION] %s paused at approval checkpoint: %s", gen_id, stage)
                _store.update_status(gen_id, "waiting_for_approval")
                _store.add_event(
                    gen_id, "approval_required",
                    agent=current_values.get("current_agent", "architect"),
                    message=f"Human approval required: {approval_req.get('title', 'Review Required')}",
                    metadata={"approval_stage": stage, "approval_request": approval_req}
                )
                await _bus.emit(
                    gen_id, "approval_required",
                    agent=current_values.get("current_agent", "architect"),
                    message=f"Human approval required: {approval_req.get('title', 'Review Required')}",
                    metadata={"approval_stage": stage, "approval_request": approval_req},
                    progress=current_values.get("workflow_progress", 25 if stage == "architecture" else 85)
                )
                return

            # Pipeline reached completion
            elapsed = perf_counter() - started_at
            _logger.info("[GENERATION] %s completed in %.1fs", gen_id, elapsed)

            final_files = final_state.get("files", {})
            project_path = final_state.get("project_path", "")

            # 1. Update Codebase Intelligence Index & Dependency Graph
            if final_files:
                global_codebase_indexer.index_project_files(project_name, final_files)
                proj_idx = global_codebase_indexer.get_project_index(project_name)
                global_dependency_graph.build_graph_from_index(project_name, proj_idx)

                # 2. Persist Project Architecture Memory
                arch = final_state.get("architecture") or {}
                if arch:
                    global_project_memory_service.save_project_memory(
                        project_id=project_name,
                        memory_type="ARCHITECTURE",
                        key="system_architecture",
                        value=arch,
                        source="ARCHITECT"
                    )

                # 3. Create Project Version Snapshot
                changed_list = [f for f, c in final_files.items() if existing_files.get(f) != c]
                global_version_manager.create_snapshot(
                    project_id=project_name,
                    files_map=final_files,
                    repair_reason=prompt,
                    changed_files=changed_list or list(final_files.keys()),
                    test_result=final_state.get("test_results", {}),
                    quality_score=final_state.get("quality_score", 100.0)
                )

            _store.update_status(gen_id, "completed")
            _store.add_event(
                gen_id, "generation_completed",
                message="Generation completed successfully",
                metadata={
                    "duration": round(elapsed, 2),
                    "project_path": project_path,
                    "files_count": len(final_files),
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
            safe_msg = f"Generation failed after {elapsed:.1f}s: {str(exc)[:150]}"
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
            # Close event bus if terminal status
            status = _store.get(gen_id, {}).get("status", "")
            if status in ("completed", "failed", "cancelled"):
                await asyncio.sleep(0.2)
                _bus.close(gen_id)

    async def approve_generation(self, gen_id: str, notes: str = "") -> dict:
        """
        Approves a paused generation at an approval checkpoint and resumes execution.
        """
        rec = _store.get(gen_id)
        if not rec:
            raise ValueError(f"Generation '{gen_id}' not found.")

        config = {"configurable": {"thread_id": gen_id}}
        state_tuple = parallel_graph.get_state(config)
        if not state_tuple:
            raise ValueError(f"No checkpoint found for generation '{gen_id}'.")

        current_values = dict(state_tuple.values or {})
        stage = current_values.get("approval_stage") or "architecture"

        _logger.info("[HITL] Approving generation %s (stage: %s)", gen_id, stage)

        # Update state on checkpointer
        update_payload = {
            "approval_status": "approved",
            "approval_required": False,
            "user_feedback": "",
            "status": "RUNNING",
            "execution_status": "RUNNING",
        }
        if stage == "architecture":
            update_payload["current_step"] = "dispatch_parallel"
        elif stage == "final":
            update_payload["current_step"] = "packaging"

        parallel_graph.update_state(config, update_payload, as_node=state_tuple.next[0] if state_tuple.next else "human_approval")

        _store.update_status(gen_id, "running")
        _store.add_event(
            gen_id, "approval_approved",
            message=f"Human approved {stage} stage. Resuming workflow...",
            metadata={"notes": notes, "stage": stage}
        )
        await _bus.emit(
            gen_id, "approval_approved",
            message=f"Human approved {stage} stage. Resuming workflow...",
            metadata={"notes": notes, "stage": stage}
        )

        # Launch resumption task
        task = asyncio.create_task(
            self._run_pipeline(gen_id, rec, is_resume=True),
            name=f"aiforge-gen-resume-{gen_id}",
        )
        _active_tasks[gen_id] = task
        task.add_done_callback(lambda t: _active_tasks.pop(gen_id, None))

        return {
            "status": "success",
            "message": f"Generation '{gen_id}' approved and resumed.",
            "generation_id": gen_id,
            "stage": stage,
            "workflow_status": "RUNNING"
        }

    async def reject_generation(self, gen_id: str, feedback: str) -> dict:
        """
        Rejects a paused generation with user feedback, revising the plan/code and resuming.
        """
        if not feedback or not feedback.strip():
            raise ValueError("Rejection feedback cannot be empty.")

        rec = _store.get(gen_id)
        if not rec:
            raise ValueError(f"Generation '{gen_id}' not found.")

        config = {"configurable": {"thread_id": gen_id}}
        state_tuple = parallel_graph.get_state(config)
        if not state_tuple:
            raise ValueError(f"No checkpoint found for generation '{gen_id}'.")

        current_values = dict(state_tuple.values or {})
        stage = current_values.get("approval_stage") or "architecture"

        _logger.info("[HITL] Rejecting generation %s with feedback: %s", gen_id, feedback[:60])

        # Update state on checkpointer with feedback
        update_payload = {
            "approval_status": "rejected",
            "approval_required": False,
            "user_feedback": feedback.strip(),
            "status": "RUNNING",
            "execution_status": "RUNNING",
        }
        if stage == "architecture":
            update_payload["current_step"] = "architect"
        elif stage == "final":
            update_payload["current_step"] = "debug"

        parallel_graph.update_state(config, update_payload, as_node=state_tuple.next[0] if state_tuple.next else "human_approval")

        _store.update_status(gen_id, "running")
        _store.add_event(
            gen_id, "approval_rejected",
            message=f"Human rejected {stage} stage. Revising with feedback: {feedback[:80]}...",
            metadata={"feedback": feedback, "stage": stage}
        )
        await _bus.emit(
            gen_id, "approval_rejected",
            message=f"Human rejected {stage} stage. Revising with feedback...",
            metadata={"feedback": feedback, "stage": stage}
        )

        # Launch resumption task
        task = asyncio.create_task(
            self._run_pipeline(gen_id, rec, is_resume=True),
            name=f"aiforge-gen-resume-{gen_id}",
        )
        _active_tasks[gen_id] = task
        task.add_done_callback(lambda t: _active_tasks.pop(gen_id, None))

        return {
            "status": "success",
            "message": f"Generation '{gen_id}' rejected with feedback. Resuming revision...",
            "generation_id": gen_id,
            "stage": stage,
            "feedback": feedback,
            "workflow_status": "RUNNING"
        }

    def get_status(self, gen_id: str) -> dict:
        """
        Retrieves full workflow status including checkpoint and approval information.
        """
        rec = _store.get(gen_id) or {}
        config = {"configurable": {"thread_id": gen_id}}
        state_tuple = parallel_graph.get_state(config)

        values = dict(state_tuple.values or {}) if state_tuple else {}
        next_nodes = list(state_tuple.next) if state_tuple else []

        is_waiting = bool(next_nodes and any(n in ("human_approval", "final_approval") for n in next_nodes))
        approval_req = values.get("approval_request") or {}

        status_str = "waiting_for_approval" if is_waiting else rec.get("status", values.get("status", "running")).lower()

        return {
            "generation_id": gen_id,
            "project_id": values.get("project_id", rec.get("project_id", gen_id)),
            "project_name": values.get("project_name", rec.get("project_id", "AIForge Project")),
            "status": status_str,
            "current_agent": values.get("current_agent", rec.get("current_agent", "planner")),
            "progress": values.get("workflow_progress", rec.get("progress", 0)),
            "approval_required": is_waiting or values.get("approval_required", False),
            "approval_status": values.get("approval_status", "pending" if is_waiting else "none"),
            "approval_stage": values.get("approval_stage", "architecture" if "human_approval" in next_nodes else "final" if "final_approval" in next_nodes else None),
            "approval_request": approval_req,
            "architecture": values.get("architecture", {}),
            "test_results": values.get("test_results", {}),
            "files_count": len(values.get("files", {})),
            "agents": rec.get("agents", []),
            "logs": rec.get("logs", []),
            "next_nodes": next_nodes,
        }

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

