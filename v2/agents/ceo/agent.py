"""
AIForge V2 – CEO Agent Class
=============================
Executive Agent executing business analysis and team resource allocation.
"""

import json
import time
import logging
from typing import Dict, Any
from v2.agents.base_agent_v2 import BaseAgentV2
from v2.agents.protocol import AgentRole
from v2.agents.ceo.prompts import CEO_SYSTEM_PROMPT
from v2.agents.ceo.models import CEOProjectEvaluation, ComplexityTier, ProjectPriority
from v2.logs.logger import global_v2_logger

_logger = logging.getLogger("aiforge.v2.ceo")


class CEOAgentV2(BaseAgentV2):
    """
    CEO Agent V2: Executive Decision Maker of AIForge V2.
    """

    def __init__(self):
        super().__init__(
            role=AgentRole.CEO,
            system_prompt=CEO_SYSTEM_PROMPT
        )

    def evaluate_project(self, prompt: str) -> CEOProjectEvaluation:
        started_at = time.perf_counter()
        _logger.info(f"CEOAgentV2: Evaluating business request: '{prompt[:60]}...'")

        raw_output = self.run(prompt)
        elapsed_ms = (time.perf_counter() - started_at) * 1000

        try:
            if "```json" in raw_output:
                json_str = raw_output.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_output:
                json_str = raw_output.split("```")[1].split("```")[0].strip()
            else:
                json_str = raw_output.strip()

            data = json.loads(json_str)
        except Exception as exc:
            _logger.warning(f"CEOAgentV2: Failed to parse LLM JSON output ({exc}). Using rule-based classification.")
            data = self._heuristic_fallback(prompt)

        p_lower = prompt.lower()
        if any(kw in p_lower for kw in ["social media", "instagram", "crm", "enterprise", "platform", "saas", "payment"]):
            data["complexity_tier"] = "enterprise"
            data["complexity_score"] = max(float(data.get("complexity_score", 8.5)), 8.5)
            data["estimated_duration_days"] = max(float(data.get("estimated_duration_days", 10.0)), 10.0)
            data["required_teams"] = ["planner", "architect", "frontend", "backend", "database", "devops", "qa", "reviewer", "security", "documentation", "deployment", "monitoring"]
        elif any(kw in p_lower for kw in ["calculator", "simple", "utility", "todo"]):
            data["complexity_tier"] = "low"
            data["complexity_score"] = min(float(data.get("complexity_score", 2.5)), 3.0)
            data["estimated_duration_days"] = 1.0
            data["required_teams"] = ["planner", "architect", "frontend", "qa", "documentation"]

        evaluation = CEOProjectEvaluation(
            project_name=data.get("project_name", "Software Application"),
            client_prompt=prompt,
            complexity_tier=ComplexityTier(data.get("complexity_tier", "medium").lower()),
            complexity_score=float(data.get("complexity_score", 5.5)),
            priority=ProjectPriority(data.get("priority", "high").lower()),
            estimated_duration_days=float(data.get("estimated_duration_days", 3.0)),
            frontend_tech=data.get("frontend_tech", "React / Vite"),
            backend_tech=data.get("backend_tech", "FastAPI"),
            database_tech=data.get("database_tech", "PostgreSQL"),
            ai_tech=data.get("ai_tech", "Ollama / Qwen2.5-Coder"),
            deployment_tech=data.get("deployment_tech", "Docker"),
            required_teams=data.get("required_teams", ["planner", "architect", "frontend", "backend", "database", "qa", "documentation"]),
            risks=data.get("risks", ["API integration latency", "Schema migration"]),
            suggested_architecture=data.get("suggested_architecture", "Decoupled FastAPI backend & React frontend")
        )

        global_v2_logger.log_agent_action(
            agent_name="ceo",
            input_text=prompt,
            output_text=json.dumps(evaluation.dict()),
            execution_time_ms=elapsed_ms,
            metadata={"tier": evaluation.complexity_tier.value, "teams_count": len(evaluation.required_teams)}
        )

        return evaluation

    def _heuristic_fallback(self, prompt: str) -> Dict[str, Any]:
        p_lower = prompt.lower()
        if "calculator" in p_lower:
            return {
                "project_name": "Calculator App",
                "complexity_tier": "low",
                "complexity_score": 2.0,
                "priority": "low",
                "estimated_duration_days": 1.0,
                "required_teams": ["planner", "architect", "frontend", "qa", "documentation"]
            }
        elif any(k in p_lower for k in ["resume", "crm", "fastapi", "react", "full stack"]):
            return {
                "project_name": "AI Resume Analyzer",
                "complexity_tier": "medium",
                "complexity_score": 5.5,
                "priority": "high",
                "estimated_duration_days": 5.0,
                "required_teams": ["planner", "architect", "frontend", "backend", "database", "qa", "documentation"]
            }
        else:
            return {
                "project_name": "Enterprise Web Platform",
                "complexity_tier": "enterprise",
                "complexity_score": 9.0,
                "priority": "high",
                "estimated_duration_days": 14.0,
                "required_teams": ["planner", "architect", "frontend", "backend", "database", "devops", "qa", "reviewer", "security", "documentation", "deployment", "monitoring"]
            }


global_ceo_agent_v2 = CEOAgentV2()
