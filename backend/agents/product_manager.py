import logging
from typing import Dict, Any, List

logger = logging.getLogger("aiforge.agents.product_manager")


class ProductManagerAgent:
    """
    ProductManagerAgent analyzes user prompts, decomposes functional & non-functional requirements,
    estimates complexity, and formulates high-level development roadmaps.
    """

    def analyze_requirements(self, prompt: str) -> Dict[str, Any]:
        """Analyzes project prompt and extracts roadmap & requirements."""
        prompt_lower = prompt.lower()

        functional_reqs = [
            "User Authentication & Authorization",
            "Core Business Logic & API Endpoints",
            "Responsive Web User Interface",
            "Database Schema & Persistence"
        ]

        if "banking" in prompt_lower or "finance" in prompt_lower:
            functional_reqs.append("Transaction Ledger & Transfer Gateway")
        elif "ecommerce" in prompt_lower or "shop" in prompt_lower:
            functional_reqs.append("Product Catalog & Stripe Payment Gateway")

        non_functional_reqs = [
            "Sub-100ms API Response Latency",
            "JWT Token Security",
            "Docker Container Deployment Readiness",
            "99.9% System Uptime"
        ]

        logger.info(f"ProductManagerAgent analyzed prompt '{prompt[:30]}...'")
        return {
            "prompt": prompt,
            "complexity": "Medium-High",
            "functional_requirements": functional_reqs,
            "non_functional_requirements": non_functional_reqs,
            "recommended_stack": "FastAPI + React + PostgreSQL + Docker"
        }


# Global ProductManagerAgent Instance
global_product_manager_agent = ProductManagerAgent()
