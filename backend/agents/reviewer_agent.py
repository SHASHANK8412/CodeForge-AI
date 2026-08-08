import json
import re
from typing import Dict, Any, List
from backend.agents.base_agent import BaseAgent


class ReviewerAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            """
You are an expert Senior Software Engineer performing code review.
You will receive generated full-stack code (frontend, backend, database).

Output MUST be valid JSON in this EXACT structure (no markdown formatting outside JSON):
{
  "status": "PASS" or "FAIL",
  "score": 0 to 100,
  "summary": "Brief explanation of evaluation",
  "issues": [
    {
      "file": "file path or layer (e.g. backend/main.py)",
      "severity": "critical" | "major" | "minor",
      "problem": "Clear explanation of the bug or flaw",
      "fix": "Specific fix instruction"
    }
  ]
}

Rules:
- Mark status as "FAIL" if there are any critical bugs, syntax errors, missing imports, or unhandled exceptions.
- Mark status as "PASS" if the code is syntactically sound and functionally complete.
""",
            task_name="reviewer",
        )

    def parse_review_json(self, raw_output: str) -> Dict[str, Any]:
        """
        Parses LLM review output into structured dictionary, falling back to heuristic parsing if needed.
        """
        # Try direct JSON extraction
        try:
            match = re.search(r'\{.*\}', raw_output, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                if "status" in data and "issues" in data:
                    return data
        except Exception:
            pass

        # Fallback heuristic parser
        issues: List[Dict[str, str]] = []
        status = "PASS"
        score = 85.0

        critical_count = raw_output.count("[Critical]") + raw_output.count('"critical"')
        major_count = raw_output.count("[Major]") + raw_output.count('"major"')
        minor_count = raw_output.count("[Minor]") + raw_output.count('"minor"')

        if critical_count > 0 or major_count > 2:
            status = "FAIL"

        score -= (critical_count * 15 + major_count * 5 + minor_count * 2)
        score = max(0.0, min(100.0, score))

        for line in raw_output.splitlines():
            line_str = line.strip()
            if any(tag in line_str for tag in ["[Critical]", "[Major]", "[Minor]"]):
                sev = "critical" if "[Critical]" in line_str else ("major" if "[Major]" in line_str else "minor")
                issues.append({
                    "file": "generated_code",
                    "severity": sev,
                    "problem": line_str,
                    "fix": "Apply code correction"
                })

        return {
            "status": status,
            "score": round(score, 1),
            "summary": "Review completed with heuristic fallback.",
            "issues": issues,
            "raw_output": raw_output
        }

    async def run_async(self, user_prompt: str, memory_context: str = "", previous_output: str = "") -> str:
        review_prompt = f"""
Generated Code to Review:
{previous_output}

Project Prompt:
{user_prompt}
"""
        return await super().run_async(review_prompt, memory_context, previous_output)