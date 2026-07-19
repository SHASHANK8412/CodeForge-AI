import ast
import json
import logging
from pathlib import Path
from backend.services.llm import generate_text_async

_logger = logging.getLogger("aiforge.performance")

SYSTEM_PATCH_PROMPT = """You are a Senior AI Patch Engineering Specialist.
Your task is to generate a minimal line-range patch to fix the faulty code in the file.
DO NOT regenerate the entire file. Generate a specific replacement code block.

You MUST return a JSON object ONLY. Do not write markdown wraps or explanations. Just return a raw JSON object matching this structure:
{
  "file": "relative/path/to/file.py",
  "start_line": 42,
  "end_line": 48,
  "replacement": "exact code lines to replace the lines from start_line to end_line (inclusive)"
}
Ensure start_line and end_line are 1-indexed line numbers containing precisely the code blocks that need replacement."""


class PatchGenerator:
    """
    Constructs localized, minimal line-range replacement patches to fix identified code issues.
    """

    def __init__(self) -> None:
        pass

    async def generate_patch(self, file_path: str, file_content: str, proposed_fix: str) -> dict | None:
        """
        Calls the LLM to write a minimal replacement patch block.
        """
        _logger.info(f"Generating patch for: {file_path}")

        user_prompt = f"""Target File: {file_path}
Proposed Fix:
{proposed_fix}

Original Code:
{file_content}"""

        try:
            response = await generate_text_async(
                system_prompt=SYSTEM_PATCH_PROMPT,
                prompt=user_prompt,
                task="testing"
            )

            # Clean response markdown wrappers
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                lines = cleaned_response.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned_response = "\n".join(lines).strip()

            patch = json.loads(cleaned_response)
            
            # Check structure
            for key in ["file", "start_line", "end_line", "replacement"]:
                if key not in patch:
                    _logger.error(f"Generated patch missing key: '{key}'")
                    return None

            # Validate patch line ranges
            patch["start_line"] = int(patch["start_line"])
            patch["end_line"] = int(patch["end_line"])
            patch["file"] = file_path

            # Basic Syntax check for Python files
            if file_path.endswith(".py"):
                if not self.validate_python_syntax(patch["replacement"]):
                    _logger.warning("INFO Patch rejected - Invalid syntax in replacement code block")
                    return None

            _logger.info("INFO Patch generated successfully")
            return patch

        except Exception as exc:
            _logger.error(f"Failed to generate patch: {exc}")
            return None

    def validate_python_syntax(self, code_block: str) -> bool:
        """
        Checks if the replacement block has valid python syntax.
        """
        try:
            # We wrap in a dummy function or parse it directly.
            # If the patch is just a few lines or a full function, ast.parse will succeed if the block is syntactically sound.
            # If there's an indentation mismatch, we try to strip it or check with a class parse.
            # We can also check if the block can compile.
            ast.parse(code_block)
            return True
        except SyntaxError:
            # Ast.parse requires valid top-level syntax. If it's a snippet inside a function, it might fail.
            # Let's try compiling with dedent or prefixing it as a block.
            try:
                # Deduct indent and try
                lines = code_block.splitlines()
                first_line_indent = len(lines[0]) - len(lines[0].lstrip()) if lines else 0
                dedented_code = "\n".join([line[first_line_indent:] if len(line) >= first_line_indent else line for line in lines])
                ast.parse(dedented_code)
                return True
            except SyntaxError:
                # If still failing, check basic parenthetical balance
                return self.check_bracket_balance(code_block)

    def check_bracket_balance(self, code: str) -> bool:
        """
        Fallback syntax check checking bracket parity.
        """
        stack = []
        mapping = {")": "(", "}": "{", "]": "["}
        for char in code:
            if char in mapping.values():
                stack.append(char)
            elif char in mapping.keys():
                if not stack or stack.pop() != mapping[char]:
                    return False
        return len(stack) == 0
