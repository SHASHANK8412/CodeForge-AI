"""
AIForge Agent Communication Output Contracts
=============================================
Defines explicit Pydantic schemas for agent communication contracts.
"""

from backend.agents.contracts.planner_output import PlannerOutput
from backend.agents.contracts.architect_output import ArchitectOutput
from backend.agents.contracts.frontend_output import FrontendOutput
from backend.agents.contracts.backend_output import BackendOutput
from backend.agents.contracts.database_output import DatabaseOutput
from backend.agents.contracts.review_output import ReviewOutput
from backend.agents.contracts.testing_output import TestingOutput

__all__ = [
    "PlannerOutput",
    "ArchitectOutput",
    "FrontendOutput",
    "BackendOutput",
    "DatabaseOutput",
    "ReviewOutput",
    "TestingOutput",
]
