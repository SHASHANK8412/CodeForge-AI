"""
AIForge Universal Base Agent Architecture
=========================================
Base class for all specialized AIForge agents.
Contains ONLY universal agent behavior:
- Reusable LLM invocation methods (generate, generate_async, run, run_async).
- Clean prompt assembly without forcing rigid global headings or coding templates.
"""

from backend.services.llm import generate_text, generate_text_async


class BaseAgent:
    """
    Base class for AIForge specialized agents.
    Provides clean LLM generation utilities without forcing global output templates.
    """

    def __init__(self, system_prompt: str, task_name: str = "general"):
        self.system_prompt = system_prompt
        self.task_name = task_name

    def generate(self, prompt: str) -> str:
        """
        One-shot generation helper directly passing system prompt and user prompt to LLM.
        """
        return generate_text(self.system_prompt, prompt, task=self.task_name)

    async def generate_async(self, prompt: str) -> str:
        """
        Async version of one-shot generation helper.
        """
        return await generate_text_async(self.system_prompt, prompt, task=self.task_name)

    def build_prompt(
        self,
        user_prompt: str,
        memory_context: str = "",
        previous_output: str = "",
    ) -> str:
        """
        Builds user prompt context while preserving prompt isolation.
        Filters past code context from memory for non-coding tasks to prevent prompt contamination.
        """
        sections = []

        if memory_context and memory_context.strip():
            # If current task is non-coding, sanitize past code snippets from memory context
            sanitized_memory = memory_context
            if self.task_name in ["explanation", "general", "resume"]:
                # Filter code snippets and code fences from past memory to prevent format leakage
                lines = memory_context.split("\n")
                filtered = [
                    line for line in lines
                    if not any(marker in line for marker in ["def ", "class ", "```", "return ", "solve_", "import "])
                ]
                sanitized_memory = "\n".join(filtered).strip()

            if sanitized_memory:
                sections.append(f"Memory Context:\n{sanitized_memory}")

        if previous_output and previous_output.strip():
            sections.append(f"Previous Agent Output:\n{previous_output}")

        sections.append(user_prompt)

        return "\n\n".join(sections)

    def run(
        self,
        user_prompt: str,
        memory_context: str = "",
        previous_output: str = "",
    ) -> str:
        final_prompt = self.build_prompt(user_prompt, memory_context, previous_output)
        return generate_text(self.system_prompt, final_prompt, task=self.task_name)

    async def run_async(
        self,
        user_prompt: str,
        memory_context: str = "",
        previous_output: str = "",
    ) -> str:
        final_prompt = self.build_prompt(user_prompt, memory_context, previous_output)
        return await generate_text_async(self.system_prompt, final_prompt, task=self.task_name)