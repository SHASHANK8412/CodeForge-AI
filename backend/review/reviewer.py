import json
import logging
from pathlib import Path
from backend.services.llm import generate_text_async
from backend.config import REVIEW_MODEL

_logger = logging.getLogger("aiforge.performance")

SYSTEM_REVIEW_PROMPT = """You are a Senior AI Software Engineer and Code Auditor.
Your task is to analyze the source code file provided and detect:
1. Logic bugs or runtime exceptions.
2. Dead code or duplicate logic.
3. Poor variable or function naming.
4. Excessively large functions (refactoring candidates).
5. Architecture violations.
6. Plaintext secrets or security issues.
7. Performance loops or blocking queries.

You MUST return a JSON array of findings ONLY. Do not write markdown wraps, markdown text, explanations or summaries. Just return a raw JSON list matching this structure:
[
  {
    "severity": "critical" | "warning" | "info",
    "file": "relative/path/to/file.py",
    "line": 42,
    "issue": "Detailed explanation of the issue found",
    "recommendation": "Detailed description of the recommendation to fix it"
  }
]
If there are no issues found, return an empty JSON array: []"""


class Reviewer:
    """
    Invokes the LLM to inspect files statically for logical errors, dead code,
    architecture compliance, and style issues, returning structured diagnostics.
    """

    def __init__(self) -> None:
        pass

    async def review_file(self, project_path: Path, relative_file_path: str) -> list[dict]:
        """
        Reviews a single file using the LLM.
        """
        full_path = project_path / relative_file_path
        if not full_path.exists():
            return []

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                code_content = f.read()
        except Exception as exc:
            _logger.warning(f"Failed to read file for review {relative_file_path}: {exc}")
            return []

        user_prompt = f"File Path: {relative_file_path}\nCode Content:\n{code_content}"

        try:
            response = await generate_text_async(
                system_prompt=SYSTEM_REVIEW_PROMPT,
                prompt=user_prompt,
                task="reviewer"
            )
            
            # Clean response markdown code block wrapper if present
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                # strip code block syntax
                lines = cleaned_response.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned_response = "\n".join(lines).strip()

            if not cleaned_response:
                return []

            findings = json.loads(cleaned_response)
            if isinstance(findings, list):
                # Ensure correct format keys
                for finding in findings:
                    finding["file"] = relative_file_path
                    finding["severity"] = finding.get("severity", "info").lower()
                    finding["line"] = int(finding.get("line", 1))
                return findings
            else:
                _logger.warning(f"LLM did not return a JSON list for {relative_file_path}: {cleaned_response}")
                return []

        except Exception as exc:
            _logger.error(f"Failed to run LLM review on {relative_file_path}: {exc}")
            return []

    async def review_project(self, project_path: Path) -> list[dict]:
        """
        Reviews all major code files in the generated project.
        """
        _logger.info("INFO Project review started")
        
        # Gather python and jsx files
        py_files = list(project_path.glob("backend/**/*.py"))
        jsx_files = list(project_path.glob("frontend/src/**/*.jsx")) + list(project_path.glob("frontend/src/**/*.js"))

        files_to_review = py_files + jsx_files
        all_findings = []

        for file_path in files_to_review:
            rel_path = str(file_path.relative_to(project_path))
            # Skip virtual environments or build outputs if scanned accidentally
            if "venv" in rel_path or "dist" in rel_path or "node_modules" in rel_path:
                continue

            findings = await self.review_file(project_path, rel_path)
            all_findings.extend(findings)

        _logger.info(f"INFO Project review completed with {len(all_findings)} issues identified")
        return all_findings
