import logging
from pathlib import Path
from backend.services.llm import generate_text

_logger = logging.getLogger("aiforge.learning")

class PromptOptimizer:
    """
    Evaluates agent feedback, dynamically rewrites prompt template files under learning/prompts/,
    and returns hot-loaded system prompts for execution.
    """

    def __init__(self, prompts_dir: str = None) -> None:
        if prompts_dir is None:
            prompts_dir = str(Path(__file__).parent / "prompts")
        self.prompts_dir = Path(prompts_dir)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self._initialize_defaults()

    def _initialize_defaults(self) -> None:
        defaults = {
            "planner": "You are a software architect planner. Design modular development checklists.",
            "backend": "You are a backend FastAPI engineer. Write clean async router views.",
            "frontend": "You are a frontend React developer. Write interactive UI components.",
            "reviewer": "You are a senior reviewer. Audit code structures for SOLID compliance."
        }
        for name, prompt in defaults.items():
            file_path = self.prompts_dir / f"{name}.txt"
            if not file_path.exists():
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(prompt)
                except Exception as e:
                    _logger.error(f"Failed to create default prompt file for {name}: {str(e)}")

    def get_system_prompt(self, agent_name: str, default_prompt: str) -> str:
        """
        Loads optimized prompt if exists on disk, falling back to default.
        """
        file_path = self.prompts_dir / f"{agent_name}.txt"
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception as e:
                _logger.error(f"Failed to read prompt file {agent_name}.txt: {str(e)}")
        return default_prompt

    def optimize_prompt(self, agent_name: str, reviewer_feedback: str) -> str:
        """
        Invokes LLM to refine the prompt based on review corrections and saves the output.
        """
        _logger.info(f"Optimizing system prompt for agent '{agent_name}' due to feedback...")
        
        current_prompt = self.get_system_prompt(agent_name, "You are a senior AI software engineer.")
        
        refine_prompt_query = f"""
Current System Prompt for '{agent_name}':
\"\"\"
{current_prompt}
\"\"\"

Critical Reviewer Feedback:
\"\"\"
{reviewer_feedback}
\"\"\"

You are an SRE Prompt Optimization Agent. Rewrite the Current System Prompt above so that the agent explicitly avoids the issues pointed out in the feedback.
Maintain the core role instructions of the agent, but make it more robust.

Output only the revised prompt text without any explanations, markdown code blocks, or preamble.
"""
        try:
            optimized = generate_text(
                system_prompt="You are an expert prompt engineer. Output only the revised prompt text directly.",
                prompt=refine_prompt_query,
                model="qwen2.5-coder:latest",
                task="general"
            ).strip()

            if optimized:
                # Save optimized prompt to disk
                file_path = self.prompts_dir / f"{agent_name}.txt"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(optimized)
                _logger.info(f"Successfully optimized and saved system prompt for {agent_name}!")
                return optimized

        except Exception as e:
            _logger.error(f"Failed to optimize system prompt via LLM: {str(e)}")
            
        return current_prompt
