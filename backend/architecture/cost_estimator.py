"""
AIForge Cloud Cost Estimator (Day 49)
=====================================
Projects monthly infrastructure costs ($/month) across AWS/GCP services based on target user scale (10K to 10M+ users).
"""

import logging
from typing import Dict, Any

_logger = logging.getLogger("aiforge.architecture.cost_estimator")


class CostEstimator:
    """
    Estimates cloud infrastructure costs for multi-tier microservices applications.
    """

    def estimate_monthly_cost(self, target_users: int = 100000) -> Dict[str, Any]:
        """
        Calculates itemized monthly infrastructure cost based on target active users.
        """
        scale_factor = target_users / 100000.0

        k8s_cost = round(120.0 * scale_factor, 2)
        db_cost = round(85.0 * scale_factor, 2)
        redis_cost = round(35.0 * scale_factor, 2)
        s3_cost = round(25.0 * scale_factor, 2)
        cdn_cost = round(45.0 * scale_factor, 2)

        total_monthly_usd = round(k8s_cost + db_cost + redis_cost + s3_cost + cdn_cost, 2)

        _logger.info(f"CostEstimator: Estimated monthly cost for {target_users:,} users -> ${total_monthly_usd}/mo")

        return {
            "target_users": target_users,
            "total_monthly_usd": total_monthly_usd,
            "breakdown_usd": {
                "compute_kubernetes": k8s_cost,
                "database_postgresql": db_cost,
                "cache_redis": redis_cost,
                "object_storage_s3": s3_cost,
                "cdn_bandwidth": cdn_cost
            }
        }


global_cost_estimator = CostEstimator()
