"""
AIForge Day 83 Infrastructure Cost Estimator Agent
==================================================
Estimates monthly cloud hosting, AI token, database storage, and bandwidth operational costs.
"""

import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.agents")


class CostEstimatorAgent:
    """
    Calculates monthly operational cost breakdown for cloud infrastructure and SaaS dependencies.
    """

    def estimate_costs(self, product_name: str) -> Dict[str, Any]:
        cost_breakdown = {
            "Cloud Hosting (AWS ECS / EC2)": 45.0,
            "Managed PostgreSQL Database": 35.0,
            "Redis Cache Service": 15.0,
            "AI Token API Calls (Ollama / Cloud LLM)": 25.0,
            "Bandwidth & Storage (S3 / CloudFront)": 15.0,
            "Domain & SSL Certificates": 10.0
        }

        total_monthly = sum(cost_breakdown.values())
        _logger.info(f"CostEstimatorAgent: Total monthly cost for '{product_name}' = ${total_monthly}/month")

        return {
            "product_name": product_name,
            "monthly_cost_breakdown_usd": cost_breakdown,
            "total_monthly_cost_usd": round(total_monthly, 2),
            "formatted_total_monthly": f"${round(total_monthly, 2)}/month"
        }


global_cost_estimator = CostEstimatorAgent()
