"""
AIForge Human Review Agent
==========================
Agent responsible for evaluating high-risk operations, generating approval requests, processing human feedback, and clarifying ambiguous requirements.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from backend.agents.base_agent import BaseAgent

_logger = logging.getLogger("aiforge.agents.human_review")


class HumanReviewAgent(BaseAgent):
    """
    Evaluates action risk, generates approval checkpoints, formats clarification questions, and translates user feedback.
    """

    HIGH_RISK_KEYWORDS = [
        "delete", "remove", "drop", "refactor", "migration", "migrate",
        "deploy", "production", "env", "environment", "secret", "auth",
        "authentication", "jwt", "upgrade", "security", "permission"
    ]

    def __init__(self, system_prompt: str = "You are the Human Review & Governance Agent for AIForge.", task_name: str = "human_review") -> None:
        super().__init__(system_prompt=system_prompt, task_name=task_name)

    def evaluate_action_risk(self, action_title: str, affected_files: List[str], description: str = "") -> Dict[str, Any]:
        """Evaluates operation risk level (High, Medium, Low) and determines if human approval is required."""
        text_content = f"{action_title} {' '.join(affected_files)} {description}".lower()
        matched_keywords = [kw for kw in self.HIGH_RISK_KEYWORDS if kw in text_content]

        if len(matched_keywords) >= 2 or any(k in text_content for k in ["production", "drop", "delete", "auth"]):
            risk_level = "High"
            approval_required = True
        elif len(matched_keywords) == 1:
            risk_level = "Medium"
            approval_required = True
        else:
            risk_level = "Low"
            approval_required = False

        return {
            "title": action_title,
            "risk": risk_level,
            "approval_required": approval_required,
            "matched_keywords": matched_keywords,
            "affected_files": affected_files,
            "reason": f"Action '{action_title}' flagged with risk level '{risk_level}' based on operation scope."
        }

    def generate_clarification(self, prompt: str) -> Dict[str, Any]:
        """Generates clarification questions when user prompts are ambiguous."""
        prompt_lower = prompt.lower()
        questions = []

        if "ecommerce" in prompt_lower or "shop" in prompt_lower:
            questions.append({
                "question": "Which payment gateway integration do you prefer?",
                "options": ["Stripe", "Razorpay", "PayPal", "Mock Payment Gateway"]
            })
            questions.append({
                "question": "Which database engine would you like to use?",
                "options": ["PostgreSQL", "SQLite", "MongoDB"]
            })
        elif "app" in prompt_lower or "system" in prompt_lower:
            questions.append({
                "question": "What primary authentication method should be implemented?",
                "options": ["JWT Bearer Tokens", "OAuth2 / Google SSO", "Session Cookies"]
            })

        if not questions:
            questions.append({
                "question": "Please clarify deployment target environment.",
                "options": ["Docker / Kubernetes", "AWS EKS", "Local Staging"]
            })

        return {
            "original_prompt": prompt,
            "is_ambiguous": True,
            "clarification_questions": questions
        }

    def convert_feedback_to_tasks(self, feedback_text: str, project_name: str = "Project") -> List[Dict[str, Any]]:
        """Converts user feedback into actionable engineering tasks."""
        lines = [line.strip() for line in feedback_text.split("\n") if line.strip()]
        tasks = []

        for idx, line in enumerate(lines, 1):
            target_agent = "Frontend Agent"
            if any(k in line.lower() for k in ["db", "database", "postgres", "sql"]):
                target_agent = "Database Agent"
            elif any(k in line.lower() for k in ["api", "backend", "auth", "latency", "speed"]):
                target_agent = "Backend Agent"
            elif any(k in line.lower() for k in ["ui", "color", "dark mode", "css", "theme"]):
                target_agent = "Frontend Agent"

            tasks.append({
                "task_id": f"fb_task_{int(time.time() * 1000)}_{idx}",
                "project_name": project_name,
                "title": f"Feedback Task: {line}",
                "assigned_agent": target_agent,
                "status": "Pending",
                "source": "Human Feedback",
                "created_at": time.time()
            })

        return tasks


global_human_review_agent = HumanReviewAgent()
