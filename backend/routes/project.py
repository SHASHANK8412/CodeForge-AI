import json
import logging
import asyncio
from pathlib import Path
from time import perf_counter

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel

from backend.graph.parallel_workflow import parallel_graph as project_graph
from backend.services.llm import stream_queue_var
from backend.generators.project_generator import ProjectGenerator

project_generator = ProjectGenerator()

router = APIRouter()
logger = logging.getLogger("aiforge.performance")


class ProjectRequest(BaseModel):
    prompt: str


# Progress percentages reported as each stage completes.
PROGRESS_STEPS = {
    "planner": 10,
    "architect": 20,
    "frontend": 35,
    "backend": 50,
    "database": 65,
    "reviewer": 80,
    "testing": 90,
    "documentation": 99,
    "completed": 100,
}


def _full_result(state: dict) -> dict:
    return {
        "plan": state.get("plan", ""),
        "architecture": state.get("architecture", ""),
        "frontend": state.get("frontend", ""),
        "backend": state.get("backend", ""),
        "database": state.get("database", ""),
        "documentation": state.get("documentation", ""),
        "tests": state.get("tests", ""),
        "review": state.get("review", ""),
        "github": state.get("github", ""),
        "error": state.get("error", ""),
    }


@router.post("/generate-project")
async def generate_project(request: ProjectRequest):
    """
    Runs the full autonomous project-generation pipeline, builds the project
    files on disk, generates metadata JSON + ZIP, and returns the response.
    """
    pipeline_started_at = perf_counter()

    result = await project_graph.ainvoke({"user_prompt": request.prompt})

    # Assemble generated code blocks into file structures
    safe_name = "".join([c if c.isalnum() or c in " -_" else "_" for c in request.prompt]).strip()
    try:
        project_generator.generate_project_structure(request.prompt, result)
    except Exception as exc:
        logger.error(f"Failed to assemble project files: {exc}")

    total_elapsed_ms = (perf_counter() - pipeline_started_at) * 1000
    print(f"Total Pipeline Time: {total_elapsed_ms:.1f}ms")
    logger.info("Total Pipeline Time: %.1fms", total_elapsed_ms)

    res_data = _full_result(result)
    res_data.update({
        "success": True,
        "project_name": request.prompt,
        "location": f"generated_projects/{safe_name}"
    })
    return res_data


@router.post("/generate-project/stream")
async def generate_project_stream(request: ProjectRequest):
    """
    Streams progress events (Server-Sent Events) while the pipeline runs.
    Assembles the final code blocks into a downloadable project folder on completion.
    """
    async def event_stream():
        pipeline_started_at = perf_counter()

        # Set up streaming queue in contextvars
        queue = asyncio.Queue()
        token = stream_queue_var.set(queue)

        # Execute the project generation graph in a background task
        graph_task = asyncio.create_task(
            project_graph.ainvoke({"user_prompt": request.prompt})
        )

        final_state = {"user_prompt": request.prompt}

        # Consume events from the queue until the graph finishes and queue is drained
        while not graph_task.done() or not queue.empty():
            try:
                # Wait briefly for queue elements so we don't block forever and can check graph_task status
                item = await asyncio.wait_for(queue.get(), timeout=0.1)
                event_type, stage, data = item

                if event_type == "chunk":
                    payload = {
                        "stage": stage,
                        "percent": PROGRESS_STEPS.get(stage, 0),
                        "chunk": data,
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
                elif event_type == "completed":
                    final_state.update(data)
                    payload = {
                        "stage": stage,
                        "percent": PROGRESS_STEPS.get(stage, 0),
                        "output": data,
                    }
                    yield f"data: {json.dumps(payload)}\n\n"

                queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as exc:  # noqa: BLE001
                error_payload = {"stage": "error", "percent": 0, "output": {"error": str(exc)}}
                yield f"data: {json.dumps(error_payload)}\n\n"
                stream_queue_var.reset(token)
                return

        # Double check if any exception occurred in the task itself
        try:
            result = await graph_task
            final_state.update(result)
        except Exception as exc:  # noqa: BLE001
            error_payload = {"stage": "error", "percent": 0, "output": {"error": str(exc)}}
            yield f"data: {json.dumps(error_payload)}\n\n"
            stream_queue_var.reset(token)
            return

        # Assemble project files to folder layout and ZIP
        safe_name = "".join([c if c.isalnum() or c in " -_" else "_" for c in request.prompt]).strip()
        try:
            project_generator.generate_project_structure(request.prompt, final_state)
        except Exception as exc:
            logger.error(f"Failed to assemble project in stream: {exc}")

        total_elapsed_ms = (perf_counter() - pipeline_started_at) * 1000
        print(f"Total Pipeline Time: {total_elapsed_ms:.1f}ms")
        logger.info("Total Pipeline Time: %.1fms", total_elapsed_ms)

        res_data = _full_result(final_state)
        res_data.update({
            "success": True,
            "project_name": request.prompt,
            "location": f"generated_projects/{safe_name}"
        })

        completed_payload = {
            "stage": "completed",
            "percent": 100,
            "output": res_data,
        }
        yield f"data: {json.dumps(completed_payload)}\n\n"

        # Reset context variable to prevent memory leak
        stream_queue_var.reset(token)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/download-project/{project_name}")
def download_project(project_name: str):
    """
    Serves the pre-compiled ZIP project file for one-click downloading.
    """
    safe_name = "".join([c if c.isalnum() or c in " -_" else "_" for c in project_name]).strip()
    zip_path = Path(__file__).resolve().parent.parent.parent / "generated_projects" / f"{safe_name}.zip"

    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Project ZIP archive not found.")

    return FileResponse(
        path=str(zip_path),
        filename=f"{safe_name}.zip",
        media_type="application/zip"
    )


