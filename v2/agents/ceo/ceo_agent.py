"""
AIForge V2 – CEO Agent
=======================
Executive Agent responsible for:
- Client Request Analysis & Scope Evaluation
- Project Complexity Estimation (1.0 to 10.0 scale)
- Resource Allocation & Agent Team Assignment
"""

import json
import logging
from typing import Dict, Any, List
from v2.agents.base_agent_v2 import BaseAgentV2
from v2.agents.protocol import AgentRole, ProjectSpecification, TaskAssignment, TaskStatus

_logger = logging.getLogger("aiforge.v2.ceo")


class CEOAgent(BaseAgentV2):
    """
    CEO Agent: Executive Leader of AIForge Autonomous AI Software Engineering Company.
    """

    def __init__(self):
        super().__init__(
            role=AgentRole.CEO,
            system_prompt="""
You are the CEO of AIForge V2 — an Autonomous AI Software Engineering Company.
Your job is to analyze client project requests, estimate technical complexity, allocate company resources,
and assemble the specialized engineering team.

Always return a JSON object with:
{
  "project_name": "...",
  "complexity_score": 7.5,
  "allocated_agents": ["planner", "architect", "frontend", "backend", "database", "qa", "devops", "learning"],
  "estimated_timeline_hours": 2.5,
  "executive_summary": "..."
}
"""
        )

    def evaluate_request(self, user_prompt: str) -> ProjectSpecification:
        _logger.info(f"CEOAgent: Evaluating client request '{user_prompt[:60]}...'")
        output = self.run(user_prompt)

        try:
            # Extract JSON block
            if "```json" in output:
                json_str = output.split("```json")[1].split("```")[0].strip()
            elif "```" in output:
                json_str = output.split("```")[1].split("```")[0].strip()
            else:
                json_str = output.strip()
            data = json.loads(json_str)
        except Exception:
            data = {
                "project_name": "Enterprise Software Module",
                "complexity_score": 6.5,
                "allocated_agents": ["planner", "architect", "frontend", "backend", "database", "reviewer", "testing", "documentation"],
                "estimated_timeline_hours": 1.5,
                "executive_summary": "Autonomous AI software engineering project execution."
            }

        allocated_roles = [AgentRole(r) for r in data.get("allocated_agents", []) if r in AgentRole._value2member_map_]

        return ProjectSpecification(
            project_id=f"proj_{int(logging.time.time() if hasattr(logging, 'time') else 1000)}",
            name=data.get("project_name", "AIForge Project"),
            client_prompt=user_prompt,
            complexity_score=float(data.get("complexity_score", 5.0)),
            allocated_agents=allocated_roles,
            estimated_timeline_hours=float(data.get("estimated_timeline_hours", 1.0))
        )


global_ceo_agent = CEOAgent()
