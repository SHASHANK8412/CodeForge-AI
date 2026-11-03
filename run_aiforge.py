#!/usr/bin/env python3
"""
AIForge command line: runs the same LangGraph pipeline as the web app (planner -> architect -> approval ->
code generation -> assembly -> review -> validation -> tests -> Execution Guardian -> final approval -> ...),
then applies the export gate.

The pipeline pauses at two human checkpoints. The architecture checkpoint can be approved with
--approve-architecture. The final checkpoint is followed by packaging, GitHub sync and deployment steps, so it
is only approved with an explicit "yes" at the prompt or --approve-final. Otherwise the run ends there: the
project has been generated and verified by then, so the result and the export gate are still reported.
"""

import argparse
import asyncio
import logging
import sys
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from backend.exporter.gate import global_export_gate
from backend.exporter.zipper import global_project_zipper
from backend.generation.manager import _approval_stage, approval_update
from backend.graph.parallel_workflow import parallel_graph
from backend.graph.project_state import ProjectState
from backend.services.llm import LLMUnavailableError

logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
_logger = logging.getLogger("aiforge.cli")

CHECKPOINTS = ("human_approval", "final_approval")


def _ask(question: str) -> bool:
    try:
        return input(f"{question} [y/N] ").strip().lower() in ("y", "yes")
    except EOFError:  # no terminal attached: never approve by default
        return False


def _error_category(exc: BaseException) -> str:
    if isinstance(exc, LLMUnavailableError):
        return "MODEL_UNAVAILABLE"
    if isinstance(exc, (TimeoutError, asyncio.TimeoutError)):
        return "TIMEOUT"
    return f"ERROR ({type(exc).__name__})"


async def _run_until_pause(graph, payload, config, on_node: Callable[[str], None]) -> None:
    """Runs the graph until it ends or pauses, reporting every node as it finishes."""
    async for update in graph.astream(payload, config=config, stream_mode="updates"):
        for node in update:
            if not node.startswith("__"):
                on_node(node)


async def run_aiforge_pipeline(
    prompt: str,
    project_name: Optional[str] = None,
    max_iterations: int = 3,
    export_zip: bool = True,
    output_dir: Optional[str] = None,
    approve_architecture: bool = False,
    approve_final: bool = False,
    ask: Callable[[str], bool] = _ask,
    graph=None,
) -> Dict[str, Any]:
    graph = graph or parallel_graph
    if not project_name:
        clean_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in prompt[:25]).strip("_")
        project_name = clean_name or "AIForge_Project"

    out_root = Path(output_dir).resolve() if output_dir else (Path.cwd() / "generated_projects").resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    proj_path = out_root / project_name

    print("\n========================================")
    print("AIForge — Autonomous Software Engineer")
    print("========================================")
    print(f"Project Name   : {project_name}")
    print(f"Target Path    : {proj_path}")
    print(f"User Request   : {prompt}")
    print("========================================\n")

    thread_id = f"cli-{uuid.uuid4().hex[:12]}"
    config = {"configurable": {"thread_id": thread_id}}
    initial_state: ProjectState = {
        "project_id": project_name,
        "generation_id": thread_id,
        "user_request": prompt,
        "user_prompt": prompt,
        "prompt": prompt,
        "project_name": project_name,
        "project_path": str(proj_path),
        "session_id": thread_id,
        "requirements": [prompt],
        "files": {},
        "dependencies": [],
        "commands": [],
        "execution_results": {},
        "test_results": {},
        "errors": [],
        "fixes": [],
        "iteration": 0,
        "max_iterations": max_iterations,
        "status": "RUNNING",
        "approval_status": "pending",
        "approval_required": False,
        "stream_events": [],
    }

    steps = []

    def on_node(node: str) -> None:
        steps.append(node)
        print(f"[{len(steps):>2}] {node} done")

    outcome = None          # set when the run stops before the graph ends
    stopped_at_final = False
    payload: Any = initial_state
    try:
        while True:
            await _run_until_pause(graph, payload, config, on_node)
            snapshot = graph.get_state(config)
            next_nodes = tuple(snapshot.next or ()) if snapshot else ()
            if not any(n in CHECKPOINTS for n in next_nodes):
                break
            values = snapshot.values or {}
            stage = _approval_stage(next_nodes, values)
            title = (values.get("approval_request") or {}).get("title", "Review required")
            print(f"\n-- Approval checkpoint ({stage}): {title}")
            if stage == "final":
                verification = (values.get("verification") or {}).get("status", "unknown")
                print(f"   Execution Guardian verification: {verification}")
                print("   Approving continues with packaging, GitHub sync and deployment steps.")
                approved = approve_final or ask("Approve the final checkpoint?")
            else:
                approved = approve_architecture or ask("Approve the architecture?")
            if not approved:
                stopped_at_final = stage == "final"
                outcome = "AWAITING_FINAL_APPROVAL" if stopped_at_final else "STOPPED_AT_ARCHITECTURE_APPROVAL"
                print(f"   Not approved: the run stops here (thread {thread_id}).\n")
                break
            graph.update_state(config, approval_update(stage), as_node=next_nodes[0])
            payload = None
    except Exception as exc:  # the pipeline itself failed: report what kind of failure it was
        outcome = _error_category(exc)
        _logger.error("Pipeline failed: %s", exc)
        print(f"\nPipeline failed: {exc}")

    snapshot = graph.get_state(config)
    final_state: Dict[str, Any] = dict(snapshot.values) if snapshot and snapshot.values else dict(initial_state)
    status = outcome or final_state.get("status", "FAILED")

    val_res = global_export_gate.validate_state(final_state)
    exec_res = final_state.get("execution_results", {}) or {}
    test_res = final_state.get("test_results", {}) or {}
    exec_status = exec_res.get("status", "NOT_RUN")
    exec_exit = exec_res.get("exit_code", -1)
    test_success = test_res.get("success", False)
    test_passed = test_res.get("passed", 0)
    test_total = test_res.get("total", test_res.get("failed", 0) + test_passed)

    overall_success = (
        (outcome is None or stopped_at_final)
        and exec_exit == 0
        and exec_status == "PASS"
        and test_success is True
        and val_res.allowed is True
    )

    export_path_str = None
    if overall_success and export_zip:
        try:
            zip_bytes = global_project_zipper.create_zip_bytes(final_state.get("files", {}) or {}, root_folder=project_name)
            target_zip = out_root / f"{project_name}.zip"
            target_zip.write_bytes(zip_bytes)
            export_path_str = str(target_zip)
            export_status_str = "SUCCESS"
        except Exception as ze:
            _logger.error("Failed to write ZIP archive to disk: %s", ze)
            export_status_str = f"FAILED ({ze})"
    elif not export_zip:
        export_status_str = "SKIPPED (--no-export)"
    else:
        export_status_str = f"DENIED ({val_res.reason})"

    print("\n----------------------------------------")
    print("PIPELINE RESULT SUMMARY")
    print("----------------------------------------")
    print(f"Project      : {project_name}")
    print(f"Status       : {status}")
    print(f"Steps run    : {len(steps)}")
    print(f"Iterations   : {final_state.get('iteration', 0)}/{max_iterations}")
    print(f"Tests        : {test_passed}/{test_total} passed")
    print(f"Execution    : {exec_status} (exit_code={exec_exit})")
    print(f"Export       : {export_status_str}")
    if export_path_str:
        print(f"Zip Location : {export_path_str}")
    print("----------------------------------------\n")

    return {
        "success": overall_success,
        "project_name": project_name,
        "project_path": str(proj_path),
        "export_path": export_path_str,
        "status": status,
        "steps": steps,
        "thread_id": thread_id,
        "iterations_used": final_state.get("iteration", 0),
        "execution_results": exec_res,
        "test_results": test_res,
        "validation_result": val_res.model_dump() if hasattr(val_res, "model_dump") else val_res.dict(),
        "final_state": final_state,
    }


def main():
    parser = argparse.ArgumentParser(description="AIForge Autonomous Software Engineer Engine CLI")
    parser.add_argument("prompt", type=str, help="What to build, in plain language")
    parser.add_argument("--project-name", type=str, default=None, help="Name of project to generate")
    parser.add_argument("--max-iterations", type=int, default=3, help="Maximum self-correction repair iterations")
    parser.add_argument("--no-export", action="store_true", help="Disable ZIP file generation")
    parser.add_argument("--output", type=str, default=None, help="Output root directory for generated projects")
    parser.add_argument("--approve-architecture", action="store_true", help="Approve the architecture checkpoint without asking")
    parser.add_argument("--approve-final", action="store_true",
                        help="Approve the final checkpoint without asking (continues with packaging, GitHub sync and deployment)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose log streaming")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    res = asyncio.run(run_aiforge_pipeline(
        prompt=args.prompt,
        project_name=args.project_name,
        max_iterations=args.max_iterations,
        export_zip=not args.no_export,
        output_dir=args.output,
        approve_architecture=args.approve_architecture,
        approve_final=args.approve_final,
    ))
    sys.exit(0 if res["success"] else 1)


if __name__ == "__main__":
    main()
