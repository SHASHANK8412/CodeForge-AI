"""
AIForge V2 – Base Agent Architecture
===================================
Base class for all enterprise agents: CEO, Manager, Planner, Architect, Development Team, QA Team, etc.
"""

import time
import logging
from typing import Dict, Any, Optional
from v2.agents.protocol import AgentRole, AgentMessage
from v2.logs.logger import global_v2_logger
from backend.services.llm import generate_text, generate_text_async

_logger = logging.getLogger("aiforge.v2.agent")


class BaseAgentV2:
    """
    Base Agent Interface for AIForge V2 Autonomous AI Software Engineering Company.
    """

    def __init__(self, role: AgentRole, system_prompt: str):
        self.role = role
        self.system_prompt = system_prompt

    def run(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> str:
        started_at = time.perf_counter()
        errors = None
        output_text = ""

        try:
            output_text = generate_text(
                system_prompt=self.system_prompt,
                prompt=input_text,
                task=self.role.value
            )
        except Exception as exc:
            errors = str(exc)
            _logger.error(f"Agent [{self.role.value}] execution error: {exc}")
            output_text = f"Agent [{self.role.value}] fallback execution triggered."
        finally:
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            global_v2_logger.log_agent_action(
                agent_name=self.role.value,
                input_text=input_text,
                output_text=output_text,
                execution_time_ms=elapsed_ms,
                errors=errors,
                metadata=context or {}
            )

        return output_text

    async def run_async(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> str:
        started_at = time.perf_counter()
        errors = None
        output_text = ""

        try:
            output_text = await generate_text_async(
                system_prompt=self.system_prompt,
                prompt=input_text,
                task=self.role.value
            )
        except Exception as exc:
            errors = str(exc)
            _logger.error(f"Agent [{self.role.value}] async execution error: {exc}")
            output_text = f"Agent [{self.role.value}] fallback async execution triggered."
        finally:
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            global_v2_logger.log_agent_action(
                agent_name=self.role.value,
                input_text=input_text,
                output_text=output_text,
                execution_time_ms=elapsed_ms,
                errors=errors,
                metadata=context or {}
            )

        return output_text
