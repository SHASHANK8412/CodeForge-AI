#!/usr/bin/env python3
"""
AIForge Autonomous Software Engineer CLI (Phase 12)
===================================================
Executes the authoritative end-to-end AIForge engineering pipeline:
USER REQUIREMENT -> PLANNER -> ARCHITECT -> GENERATION -> ASSEMBLY -> RUNNER -> TESTER -> DEBUGGER -> MEMORY -> EXPORT GATE -> EXPORT.
"""

import sys
import argparse
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from backend.graph.project_state import ProjectState
from backend.graph.parallel_workflow import parallel_graph
from backend.exporter.gate import global_export_gate
from backend.exporter.zipper import global_project_zipper

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
_logger = logging.getLogger("aiforge.cli")


async def run_aiforge_pipeline(
    prompt: str,
    project_name: Optional[str] = None,
    max_iterations: int = 3,
    export_zip: bool = True,
    output_dir: Optional[str] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Executes the authoritative parallel_graph pipeline and evaluates strict export gating.
    """
    if not project_name:
        clean_name = "".join([c if c.isalnum() or c in "-_" else "_" for c in prompt[:25]]).strip("_")
        project_name = clean_name if clean_name else "AIForge_Project"

    out_root = Path(output_dir).resolve() if output_dir else (Path.cwd() / "generated_projects").resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    proj_path = out_root / project_name
    proj_path.mkdir(parents=True, exist_ok=True)


    print("\n========================================")
    print("AIForge — Autonomous Software Engineer")
    print("========================================")
    print(f"Project Name   : {project_name}")
    print(f"Target Path    : {proj_path}")
    print(f"User Request   : {prompt}")
    print("========================================\n")

    initial_state: ProjectState = {
        "user_request": prompt,
        "project_name": project_name,
        "project_path": str(proj_path),
        "technology_stack": "FastAPI Python React PostgreSQL",
        "requirements": [prompt],
        "files": {},
        "dependencies": {},
        "commands": {},
        "execution_results": {},
        "test_results": {},
        "errors": [],
        "fixes": [],
        "iteration": 0,
        "max_iterations": max_iterations,
        "status": "NOT_STARTED",
        "stream_events": []
    }

    print("[1/8] Planning...")
    print("[2/8] Architecture...")
    print("[3/8] Code Generation...")
    print("[4/8] Project Assembly...")

    # Execute authoritative LangGraph parallel workflow
    try:
        final_state = await parallel_graph.ainvoke(initial_state)
    except Exception as e:
        _logger.error(f"Pipeline execution encountered unhandled error: {e}")
        final_state = dict(initial_state)
        final_state["status"] = "SECURITY_ERROR"
        final_state["errors"] = [str(e)]

    print("[5/8] Execution...")
    print("[6/8] Testing...")
    print("[7/8] Self-Correction...")
    print("[8/8] Verification & Export...")

    # Authoritative Verification & Export Gate Evaluation
    val_res = global_export_gate.validate_state(final_state)
    
    exec_res = final_state.get("execution_results", {}) or {}
    test_res = final_state.get("test_results", {}) or {}
    status = final_state.get("status", "FAILED")

    exec_status = exec_res.get("status", "FAIL")
    exec_exit = exec_res.get("exit_code", -1)
    test_success = test_res.get("success", False)
    test_passed = test_res.get("passed", 0)
    test_total = test_res.get("total", test_res.get("failed", 0) + test_passed)

    overall_success = (
        exec_exit == 0 and
        exec_status == "PASS" and
        test_success is True and
        status == "PASS" and
        val_res.allowed is True
    )

    export_path_str = None
    if overall_success and export_zip:
        try:
            files_map = final_state.get("files", {}) or {}
            zip_bytes = global_project_zipper.create_zip_bytes(files_map, root_folder=project_name)
            target_zip = out_root / f"{project_name}.zip"
            target_zip.write_bytes(zip_bytes)
            export_path_str = str(target_zip)
            export_status_str = "SUCCESS"
        except Exception as ze:
            _logger.error(f"Failed to write ZIP archive to disk: {ze}")
            export_status_str = f"FAILED ({ze})"
    else:
        export_status_str = f"DENIED ({val_res.reason})"

    print("\n----------------------------------------")
    print("PIPELINE RESULT SUMMARY")
    print("----------------------------------------")
    print(f"Project      : {project_name}")
    print(f"Status       : {status}")
    print(f"Iterations   : {final_state.get('iteration', 1)}/{max_iterations}")
    print(f"Tests        : {test_passed}/{test_total} Passed")
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
        "iterations_used": final_state.get("iteration", 1),
        "execution_results": exec_res,
        "test_results": test_res,
        "validation_result": val_res.model_dump() if hasattr(val_res, "model_dump") else val_res.dict(),
        "final_state": final_state
    }


def main():
    parser = argparse.ArgumentParser(description="AIForge Autonomous Software Engineer Engine CLI")
    parser.add_argument("prompt", type=str, help="Natural language application specification requirement prompt")
    parser.add_argument("--project-name", type=str, default=None, help="Name of project to generate")
    parser.add_argument("--max-iterations", type=int, default=3, help="Maximum self-correction repair iterations")
    parser.add_argument("--no-export", action="store_true", help="Disable ZIP file generation")
    parser.add_argument("--output", type=str, default=None, help="Output root directory for generated projects")
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
        verbose=args.verbose
    ))

    sys.exit(0 if res["success"] else 1)


if __name__ == "__main__":
    main()
