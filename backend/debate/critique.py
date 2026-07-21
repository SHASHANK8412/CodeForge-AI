import logging
from backend.services.llm import generate_text

_logger = logging.getLogger("aiforge.debate")

class CritiqueEvaluator:
    """
    Orchestrates cross-agent reviews where one agent evaluates another's proposal
    (e.g., Frontend critiques Backend architecture, Backend critiques Database).
    """

    def __init__(self) -> None:
        pass

    async def generate_critique(
        self,
        agent_name: str,
        target_agent: str,
        target_proposal: str
    ) -> str:
        """
        Queries Ollama to perform peer critique on structural parameters.
        """
        _logger.info(f"Agent '{agent_name}' is critiquing '{target_agent}'...")

        prompt = f"""
You are the {agent_name} Agent. Review the design proposal submitted by the {target_agent} Agent:
---
{target_proposal}
---

Identify:
1. Missing components or incorrect assumptions.
2. Potential bottlenecks, performance lags, or security concerns.
3. Code smells or scalability limits.

Provide a concise, professional peer critique. Keep it under 150 words.
"""
        try:
            critique = generate_text(
                system_prompt=f"You are a Senior {agent_name} Specialist on an SRE team.",
                prompt=prompt,
                model="qwen2.5-coder:latest",
                task="general"
            ).strip()
        except Exception as e:
            _logger.error(f"Ollama query failed for {agent_name} critique: {str(e)}")
            # Fallback peer critique
            critique = f"Review of '{target_agent}' looks standard. Verify input validation scales correctly under load."

        return critique
