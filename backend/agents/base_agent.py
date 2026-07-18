from backend.services.llm import generate_text, generate_text_async


class BaseAgent:
    """
    Base class for every AIForge agent.

    All specialized agents (Planner, Architect, Frontend, Backend,
    Database, Documentation, Testing, Reviewer, GitHub, etc.) inherit
    from this class so they share a single, consistent way to talk to
    the LLM (via `generate`/`run`) and to build prompts (`build_prompt`).
    """

    def __init__(self, system_prompt: str, task_name: str = "general"):
        self.system_prompt = system_prompt
        self.task_name = task_name

    def generate(self, prompt: str) -> str:
        """
        Simple one-shot generation helper.

        Several agents (Backend, Database, Documentation, GitHub, ...)
        already build a single, fully-formed prompt themselves and just
        need the raw LLM response back. This method reuses the same
        `generate_text` service as `run()` so behavior (model selection,
        caching, fallback handling) stays identical across all agents.
        """
        return generate_text(self.system_prompt, prompt, task=self.task_name)

    async def generate_async(self, prompt: str) -> str:
        """
        Async version of the one-shot generation helper.
        """
        return await generate_text_async(self.system_prompt, prompt, task=self.task_name)

    def build_prompt(
        self,
        user_prompt: str,
        memory_context: str = "",
        previous_output: str = "",
    ) -> str:

        sections = []

        if memory_context:
            sections.append(f"Memory Context\n{memory_context}")

        if previous_output:
            sections.append(f"Previous Agent Output\n{previous_output}")

        sections.append(f"Current Task\n{user_prompt}")
        sections.append(
            "Response Format\n"
            "- Use Markdown headings and bullet points.\n"
            "- Start with a brief one-line summary.\n"
            "- Keep the response concise and structured.\n"
            "- Use code fences for code, commands, and config.\n"
            "- Avoid filler, greetings, and repeated wording."
        )

        return "\n\n".join(sections)

    def run(
        self,
        user_prompt: str,
        memory_context: str = "",
        previous_output: str = "",
    ):
        final_prompt = self.build_prompt(user_prompt, memory_context, previous_output)
        return generate_text(self.system_prompt, final_prompt, task=self.task_name)

    async def run_async(
        self,
        user_prompt: str,
        memory_context: str = "",
        previous_output: str = "",
    ):
        final_prompt = self.build_prompt(user_prompt, memory_context, previous_output)
        return await generate_text_async(self.system_prompt, final_prompt, task=self.task_name)