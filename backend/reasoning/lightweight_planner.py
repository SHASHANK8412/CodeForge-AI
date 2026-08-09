"""
AIForge Lightweight Task Planner & Plan Validator
================================================
Generates concise internal TaskPlan structures for PLANNED execution strategy.
Exposes zero hidden chain-of-thought traces to the user.
"""

import json
import logging
from typing import Dict, Any, List, Optional

from backend.reasoning.models import TaskPlan, TaskPlanStep

_logger = logging.getLogger("aiforge.reasoning.lightweight_planner")

MAX_PLAN_STEPS = 8


class PlanValidator:
    """
    Validates generated TaskPlan instances.
    """

    def validate(self, plan: TaskPlan) -> bool:
        if not plan:
            return False

        if not plan.goal or not plan.goal.strip():
            _logger.warning("[PlanValidator] Rejected plan: empty goal")
            return False

        if not plan.steps or len(plan.steps) == 0:
            _logger.warning("[PlanValidator] Rejected plan: no steps provided")
            return False

        if len(plan.steps) > MAX_PLAN_STEPS:
            _logger.warning(f"[PlanValidator] Rejected plan: step count ({len(plan.steps)}) exceeds MAX_PLAN_STEPS ({MAX_PLAN_STEPS})")
            return False

        step_descs = set()
        for step in plan.steps:
            if not step.description or not step.description.strip():
                _logger.warning("[PlanValidator] Rejected plan: empty step description")
                return False
            if step.description.strip().lower() in step_descs:
                _logger.warning(f"[PlanValidator] Rejected plan: duplicate step description '{step.description}'")
                return False
            step_descs.add(step.description.strip().lower())

        return True


class LightweightPlanner:
    """
    Constructs concise engineering TaskPlan instances for PLANNED strategy execution.
    """

    def __init__(self):
        self.validator = PlanValidator()

    def build_plan(
        self,
        prompt: str,
        intent: str,
        context_result: Optional[Any] = None
    ) -> Optional[TaskPlan]:
        """
        Builds a structured TaskPlan for a complex user prompt.
        Uses deterministic pattern matching for common architecture tasks to ensure fast execution (< 2ms).
        """
        if not prompt or not prompt.strip():
            return None
        try:
            prompt_clean = prompt.strip()
            prompt_lower = prompt_clean.lower()

            # Pattern 1: JWT / Authentication Design
            if "jwt" in prompt_lower or "auth" in prompt_lower or "authentication" in prompt_lower:
                goal = f"Design and implement authentication system for: {prompt_clean[:60]}"
                steps = [
                    TaskPlanStep(id=1, description="Define user identity models and token payload structure", agent_hint="CodingAgent"),
                    TaskPlanStep(id=2, description="Implement JWT access and refresh token generation utilities", agent_hint="CodingAgent"),
                    TaskPlanStep(id=3, description="Create authentication endpoint routes (login, token refresh, logout)", agent_hint="CodingAgent"),
                    TaskPlanStep(id=4, description="Define request authorization dependencies and role-based guards", agent_hint="CodingAgent"),
                    TaskPlanStep(id=5, description="Add token revocation and error handling strategy", agent_hint="CodingAgent")
                ]
                constraints = ["Must use secure password hashing", "Token expiry must be configurable"]
                dependencies = ["PyJWT", "Passlib/Bcrypt", "FastAPI Security"]

            # Pattern 2: Database Schema / E-Commerce Backend Design
            elif "schema" in prompt_lower or "database" in prompt_lower or "ecommerce" in prompt_lower or "postgresql" in prompt_lower:
                goal = f"Design relational database schema and architecture for: {prompt_clean[:60]}"
                steps = [
                    TaskPlanStep(id=1, description="Identify core domain entities and primary key models", agent_hint="CodingAgent"),
                    TaskPlanStep(id=2, description="Define 3NF table schemas, data types, and foreign key relationships", agent_hint="CodingAgent"),
                    TaskPlanStep(id=3, description="Design indexes and constraints for query optimization", agent_hint="CodingAgent"),
                    TaskPlanStep(id=4, description="Provide SQL DDL statements and migration scripts", agent_hint="CodingAgent")
                ]
                constraints = ["Ensure 3NF normalization", "Include timestamps and foreign keys"]
                dependencies = ["PostgreSQL", "SQLAlchemy"]

            # Pattern 3: Multi-Module Debugging / Error Refactoring
            elif intent == "DEBUGGING" or "debug" in prompt_lower or "refactor" in prompt_lower or "fix" in prompt_lower:
                goal = f"Diagnose, isolate, and refactor code issue: {prompt_clean[:60]}"
                steps = [
                    TaskPlanStep(id=1, description="Analyze stack trace, error logs, and module interaction points", agent_hint="DebugAgent"),
                    TaskPlanStep(id=2, description="Identify root cause and edge cases breaking execution", agent_hint="DebugAgent"),
                    TaskPlanStep(id=3, description="Formulate corrective code patch and parameter validation", agent_hint="CodingAgent"),
                    TaskPlanStep(id=4, description="Provide refactored code and regression test assertions", agent_hint="CodingAgent")
                ]
                constraints = ["Preserve existing public function signatures"]
                dependencies = ["Python Logging", "Pytest"]

            # Generic Engineering Plan Fallback
            else:
                goal = f"Execute multi-step engineering task: {prompt_clean[:60]}"
                steps = [
                    TaskPlanStep(id=1, description="Analyze task requirements and architectural constraints", agent_hint="ExplanationAgent"),
                    TaskPlanStep(id=2, description="Structure core components and data structures", agent_hint="CodingAgent"),
                    TaskPlanStep(id=3, description="Implement complete, production-grade code solution", agent_hint="CodingAgent"),
                    TaskPlanStep(id=4, description="Verify implementation completeness and edge cases", agent_hint="CodingAgent")
                ]
                constraints = ["Modular design", "Production quality"]
                dependencies = []

            plan = TaskPlan(
                goal=goal,
                steps=steps,
                constraints=constraints,
                dependencies=dependencies,
                expected_output="Structured architectural specification and code implementation",
                is_valid=True
            )

            if self.validator.validate(plan):
                _logger.info(f"[LightweightPlanner] Built valid TaskPlan with {len(steps)} steps for '{prompt_clean[:40]}'")
                return plan
            else:
                _logger.warning("[LightweightPlanner] Plan failed validation; falling back to None")
                return None

        except Exception as e:
            _logger.error(f"[LightweightPlanner] Error building TaskPlan: {e}; falling back to None")
            return None


global_lightweight_planner = LightweightPlanner()
global_plan_validator = PlanValidator()
