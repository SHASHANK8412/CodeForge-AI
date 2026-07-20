import logging
from pathlib import Path
from typing import Dict, Any, List
from backend.services.llm import generate_text

_logger = logging.getLogger("aiforge.learning")

class ReflectionEngine:
    """
    Formulates a project retrospective post-execution (reflection.md),
    outlining successful steps, diagnostic faults, and refactoring guidelines.
    """

    def __init__(self, reflection_dir: str = None) -> None:
        if reflection_dir is None:
            reflection_dir = str(Path(__file__).parent / "reflection")
        self.reflection_dir = Path(reflection_dir)
        self.reflection_dir.mkdir(parents=True, exist_ok=True)

    def generate_reflection(
        self,
        project_name: str,
        techs: List[str],
        mistakes: List[str],
        success: bool = True
    ) -> str:
        """
        Submits retrospect details to LLM and saves reflection.md.
        """
        _logger.info(f"Generating post-project reflection for '{project_name}'...")

        prompt = f"""
Project Retrospective Data:
- Project Name: {project_name}
- Stack: {", ".join(techs)}
- Outages/Mistakes: {", ".join(mistakes) if mistakes else "None"}
- Completed successfully: {success}

Write a structured reflection markdown block answering:
1. What went well?
2. What failed or degraded?
3. What should change or be optimized in future builds?

Do not include code blocks or chat greetings, output only the raw markdown body.
"""
        try:
            reflection_text = generate_text(
                system_prompt="You are an SRE Team Lead. Write a concise reflection report.",
                prompt=prompt,
                model="qwen2.5-coder:latest",
                task="general"
            ).strip()
        except Exception as e:
            _logger.error(f"Ollama reflection query failed: {str(e)}")
            # Fallback retrospective text
            reflection_text = f"""# Reflection: {project_name}
## 1. What went well
* Successfully initialized framework code templates for {", ".join(techs)}.
## 2. What failed or degraded
* Outages: {", ".join(mistakes) if mistakes else "None"}.
## 3. Recommended Changes
* Optimize import chains and enable background validation sweeps.
"""

        # Save to file
        file_path = self.reflection_dir / "reflection.md"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(reflection_text)
            _logger.info("Successfully updated global reflection.md retrospective.")
        except Exception as e:
            _logger.error(f"Failed to write SRE reflection.md: {str(e)}")

        return reflection_text
