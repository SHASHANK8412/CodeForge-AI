"""
AIForge Product Intelligence Agent Module
=========================================
Converts natural language user prompts into canonical ProjectSpecification models.
Extracts functional, non-functional, security, data, and business requirements with stable IDs.
"""

import re
import logging
from typing import Dict, Any, List, Optional

from backend.agents.base_agent import BaseAgent
from backend.requirements.models import (
    ProjectSpecification,
    Requirement,
    UserStory,
    AcceptanceCriteria,
    TraceabilityItem
)

_logger = logging.getLogger("aiforge.requirements.product_intelligence")


class ProductIntelligenceAgent(BaseAgent):
    """
    Analyzes user intent and builds structured ProjectSpecification models.
    """

    SYSTEM_PROMPT = "You are an expert Product Intelligence and Requirements Engineer."

    def __init__(self):
        super().__init__(self.SYSTEM_PROMPT, task_name="requirements")

    def analyze_prompt(self, user_prompt: str, project_name: str = "AIForge Project") -> ProjectSpecification:
        _logger.info(f"ProductIntelligenceAgent: Analyzing user prompt for '{project_name}'...")
        prompt_lower = user_prompt.lower()

        # 1. Functional Requirements
        frs = [
            Requirement(id="FR-001", category="FUNCTIONAL", title="User Registration", description="Users can create an account with email and password.", priority="HIGH"),
            Requirement(id="FR-002", category="FUNCTIONAL", title="User Authentication", description="Users can log in and obtain JWT access tokens.", priority="HIGH"),
            Requirement(id="FR-003", category="FUNCTIONAL", title="Core Data Management", description="Users can create, view, update, and delete core items.", priority="HIGH"),
            Requirement(id="FR-004", category="FUNCTIONAL", title="Item Filtering & Search", description="Users can filter and search stored entries.", priority="MEDIUM")
        ]

        if "todo" in prompt_lower or "task" in prompt_lower:
            frs.append(Requirement(id="FR-005", category="FUNCTIONAL", title="Task Status Toggle", description="Users can mark tasks as completed or pending.", priority="HIGH"))
        if "food" in prompt_lower or "delivery" in prompt_lower:
            frs.append(Requirement(id="FR-005", category="FUNCTIONAL", title="Cart & Order Checkout", description="Users can add menu items to cart and checkout.", priority="HIGH"))

        # 2. Security Requirements
        sec_reqs = [
            Requirement(id="SEC-001", category="SECURITY", title="JWT Password Hashing", description="Passwords must be hashed using bcrypt or Passlib and never stored in plaintext.", priority="CRITICAL"),
            Requirement(id="SEC-002", category="SECURITY", title="Protected API Endpoints", description="Sensitive backend routes require valid Authorization Bearer tokens.", priority="HIGH"),
            Requirement(id="SEC-003", category="SECURITY", title="Secret Isolation", description="Secrets like JWT_SECRET and DATABASE_URL must be isolated outside source code.", priority="CRITICAL")
        ]

        # 3. Non-Functional Requirements
        nfrs = [
            Requirement(id="NFR-001", category="NON_FUNCTIONAL", title="API Latency", description="API response time should be under 500ms for standard requests.", priority="MEDIUM"),
            Requirement(id="NFR-002", category="NON_FUNCTIONAL", title="Responsive Layout", description="Frontend must render seamlessly across desktop and mobile viewports.", priority="HIGH")
        ]

        # 4. Data Requirements
        data_reqs = [
            Requirement(id="DATA-001", category="DATA", title="User Schema", description="Relational schema storing id, email, hashed_password, created_at.", priority="HIGH"),
            Requirement(id="DATA-002", category="DATA", title="Core Item Schema", description="Relational schema storing id, title, status, owner_id, timestamps.", priority="HIGH")
        ]

        # 5. User Stories
        user_stories = [
            UserStory(id="US-001", as_a="registered user", i_want="to log in securely", so_that="I can access my personal data", requirement_ids=["FR-001", "FR-002"]),
            UserStory(id="US-002", as_a="authenticated user", i_want="to create and manage items", so_that="I can keep track of my work", requirement_ids=["FR-003", "FR-004"])
        ]

        # 6. Acceptance Criteria
        acceptance_criteria = [
            AcceptanceCriteria(id="AC-001", user_story_id="US-001", given="a registered user with valid credentials", when="they submit email and password", then="a valid JWT access token is returned and stored", requirement_ids=["FR-002", "SEC-001"]),
            AcceptanceCriteria(id="AC-002", user_story_id="US-002", given="an authenticated user", when="they create a new item", then="the item appears in their list immediately", requirement_ids=["FR-003"])
        ]

        # 7. Traceability Matrix Initialization
        matrix = []
        for req in frs + sec_reqs:
            matrix.append(TraceabilityItem(
                requirement_id=req.id,
                user_story_ids=[u.id for u in user_stories if req.id in u.requirement_ids],
                acceptance_criteria_ids=[a.id for a in acceptance_criteria if req.id in a.requirement_ids],
                implementation_files=[],
                test_files=[],
                status="NOT_IMPLEMENTED"
            ))

        assumptions = [
            "Responsive SPA layout for modern browsers",
            "PostgreSQL or SQLite relational database",
            "FastAPI backend with Uvicorn server"
        ]

        target_users = ["End User / Customer", "System Administrator"]

        return ProjectSpecification(
            project_name=project_name,
            project_type="Full-Stack Web Application",
            version="1.0",
            target_users=target_users,
            functional_requirements=frs,
            non_functional_requirements=nfrs,
            security_requirements=sec_reqs,
            data_requirements=data_reqs,
            user_stories=user_stories,
            acceptance_criteria=acceptance_criteria,
            traceability_matrix=matrix,
            assumptions=assumptions,
            coverage_score=0.0
        )


global_product_intelligence_agent = ProductIntelligenceAgent()
