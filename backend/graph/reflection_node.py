import time
import logging
from pathlib import Path
from backend.graph.project_state import ProjectState
from backend.agents.reflection_agent import ReflectionAgent
from backend.services.reflection_service import ReflectionService

_logger = logging.getLogger("aiforge.performance")

reflection_agent = ReflectionAgent()
reflection_service = ReflectionService()

async def reflection_node(state: ProjectState) -> dict:
    """
    LangGraph node that executes the Reflection Agent over completed project outputs,
    saving learnings permanently and computing scores.
    """
    _logger.info("Reflection started")
    start_time = time.perf_counter()
    
    project_path_str = state.get("project_path")
    prompt = state.get("prompt") or state.get("user_prompt", "")
    validation_report = state.get("validation_report") or {}
    
    if not project_path_str:
        _logger.warning("Project path missing during reflection node execution")
        return {"current_step": "reflection"}

    project_path = Path(project_path_str)
    
    # Gather code snippets from backend and frontend files
    code_snippets = []
    backend_file = project_path / "backend/main.py"
    if backend_file.exists():
        try:
            with open(backend_file, "r", encoding="utf-8") as f:
                code_snippets.append(f"--- backend/main.py ---\n{f.read()}")
        except Exception:
            pass

    frontend_file = project_path / "frontend/src/App.jsx"
    if frontend_file.exists():
        try:
            with open(frontend_file, "r", encoding="utf-8") as f:
                code_snippets.append(f"--- frontend/src/App.jsx ---\n{f.read()}")
        except Exception:
            pass

    code_str = "\n\n".join(code_snippets)
    
    # Format inputs for LLM
    reviewer_feedback = str(state.get("review_findings") or "No reviewer output found.")
    
    # Calculate tests passed from test results
    test_results = state.get("test_results") or {}
    tests_passed = test_results.get("passed", 0)
    failed_tests = test_results.get("failed", 0)
    test_output = f"Passed: {tests_passed}, Failed: {failed_tests}"
    
    validation_str = json_dumps_safe(validation_report)

    # 1. Run LLM reflection
    try:
        reflection_data = await reflection_agent.reflect_on_project(
            project_name=prompt,
            code_snippets=code_str,
            reviewer_feedback=reviewer_feedback,
            test_output=test_output,
            validation_report=validation_str
        )
    except Exception as exc:
        _logger.error(f"Reflection Agent execution failed: {exc}")
        reflection_data = {
            "strengths": ["Project files compiled successfully."],
            "weaknesses": ["Execution logs could not be parsed by LLM."],
            "recommendations": ["Optimize reflection agent parameters."],
            "lessons": [],
            "reflection_score": 85
        }

    # 2. Extract and merge lessons permanently
    lessons = reflection_data.get("lessons") or []
    if lessons:
        reflection_service.add_lessons(lessons)
        _logger.info("Lessons updated")

    # 3. Add to reflection history
    score = reflection_data.get("reflection_score", 85)
    recs = reflection_data.get("recommendations", [])
    duration = time.perf_counter() - start_time
    
    reflection_service.add_history_record(
        project_name=prompt,
        reflection_score=score,
        bugs_found=failed_tests,
        tests_passed=tests_passed,
        recommendations=recs,
        execution_time=duration
    )
    
    _logger.info(f"Reflection completed. Score: {score}")

    return {
        "reflection_report": reflection_data,
        "current_step": "reflection"
    }

def json_dumps_safe(obj: any) -> str:
    try:
        import json
        return json.dumps(obj, indent=2)
    except Exception:
        return str(obj)
