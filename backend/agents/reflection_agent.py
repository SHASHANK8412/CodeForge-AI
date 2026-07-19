import json
import logging
import re
from backend.agents.base_agent import BaseAgent

_logger = logging.getLogger("aiforge.performance")

class ReflectionAgent(BaseAgent):
    """
    Analyzes generated project outputs (code, review logs, test failures, validations)
    to extract strengths, weaknesses, lessons, and computes a quality score.
    """

    def __init__(self) -> None:
        super().__init__(
            system_prompt="""
You are a Principal AI Systems Engineer and Senior Technical Architect.
Your task is to analyze a completed software project's generated code, test outputs, and reviewer feedback to evaluate its quality and extract reusable lessons.

You must output a JSON object with exactly these keys:
{
    "strengths": ["list of strings highlighting positive code traits"],
    "weaknesses": ["list of strings detailing flaws, bugs, or omissions"],
    "recommendations": ["list of actionable improvements for future generations"],
    "lessons": [
        {
            "problem": "Specific short description of a bug/issue/omission",
            "lesson": "Reusable software engineering rule/best practice to solve it"
        }
    ],
    "reflection_score": 85
}

Rules:
1. Return ONLY the raw JSON block. No markdown wrapper, no explanations outside the JSON.
2. The reflection_score must be an integer between 0 and 100.
3. Keep lessons concise and reusable.
            """,
            task_name="reflection"
        )

    async def reflect_on_project(
        self,
        project_name: str,
        code_snippets: str,
        reviewer_feedback: str,
        test_output: str,
        validation_report: str
    ) -> dict:
        """
        Executes reflection analysis over project context metrics.
        """
        prompt = f"""
Project Name: {project_name}

=== Generated Code Snippets ===
{code_snippets}

=== Reviewer Feedback ===
{reviewer_feedback}

=== Test Run Output ===
{test_output}

=== Validation Report ===
{validation_report}
"""
        _logger.info("Reflection Agent started LLM analysis...")
        raw_response = await self.generate_async(prompt)
        
        # Parse JSON output with fallback safety
        try:
            # Clean possible markdown block formatting
            clean_str = raw_response.strip()
            if clean_str.startswith("```"):
                # strip out ```json and ```
                clean_str = re.sub(r"^```(?:json)?\n", "", clean_str)
                clean_str = re.sub(r"\n```$", "", clean_str)
            
            data = json.loads(clean_str)
            
            # Enforce key constraints
            required_keys = {"strengths", "weaknesses", "recommendations", "lessons", "reflection_score"}
            for key in required_keys:
                if key not in data:
                    data[key] = [] if key != "reflection_score" else 85
                    
            if not isinstance(data["reflection_score"], (int, float)):
                data["reflection_score"] = 85
                
            return data
            
        except Exception as exc:
            _logger.warning(f"Failed to parse LLM reflection JSON, returning graceful default: {exc}")
            # Try a regex search for a JSON-like structure
            json_match = re.search(r"\{.*\}", raw_response, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    return data
                except Exception:
                    pass
            
            return {
                "strengths": ["Code structure assembled successfully."],
                "weaknesses": ["Parsing LLM outputs was unsuccessful."],
                "recommendations": ["Ensure JSON response structures are valid."],
                "lessons": [{"problem": "Unparsable reflection payload", "lesson": "Use clean schema validators"}],
                "reflection_score": 80
            }
