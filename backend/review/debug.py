import json
import logging
from backend.services.llm import generate_text_async

_logger = logging.getLogger("aiforge.performance")

SYSTEM_DEBUG_PROMPT = """You are a Senior AI Debugging Specialist.
Your task is to analyze test failure logs, tracebacks, failing file paths, and output details to identify the root cause of the error.
You MUST explain WHY the error occurred and supply a concrete code fix proposal.

Return a JSON object ONLY. Do not write markdown wraps, headers, or explanations. Just return a raw JSON object matching this structure:
{
  "root_cause": "Short summary of why the failure occurred",
  "explanation": "Detailed explanation of the mismatch or exception",
  "proposed_fix": "Exact description of how to fix the code, including the replacement lines",
  "confidence_score": 0.95
}
Ensure confidence_score is a float between 0.0 and 1.0."""


class DebugAgent:
    """
    Analyzes traceback errors and test failures to isolate root causes and provide proposed fixes.
    """

    def __init__(self) -> None:
        pass

    async def debug_failures(self, traceback: str, pytest_output: str, failing_files: list[str]) -> dict:
        """
        Calls the LLM to inspect failures and outline a repair strategy.
        """
        _logger.info("INFO Debug Agent started")

        user_prompt = f"""Failing Files: {failing_files}

Pytest Log:
{pytest_output}

Traceback:
{traceback}"""

        try:
            response = await generate_text_async(
                system_prompt=SYSTEM_DEBUG_PROMPT,
                prompt=user_prompt,
                task="testing"
            )

            # Strip markdown code formatting if present
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                lines = cleaned_response.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned_response = "\n".join(lines).strip()

            data = json.loads(cleaned_response)
            
            # Set defaults if keys are missing
            data["root_cause"] = data.get("root_cause", "Assertion error or exception during test run")
            data["explanation"] = data.get("explanation", "Test execution failed to match expectation.")
            data["proposed_fix"] = data.get("proposed_fix", "")
            data["confidence_score"] = float(data.get("confidence_score", 0.7))
            
            _logger.info(f"INFO Debug completed with confidence: {data['confidence_score']}")
            return data

        except Exception as exc:
            _logger.error(f"Failed to debug failures: {exc}")
            return {
                "root_cause": "Failed to invoke debug agent",
                "explanation": str(exc),
                "proposed_fix": "",
                "confidence_score": 0.0
            }
