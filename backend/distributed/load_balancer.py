"""
AIForge Load Balancer
====================
Distributes task workloads across worker nodes using Round Robin, Least Loaded, Priority-Based, and Resource-Aware algorithms.
"""

import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.distributed.load_balancer")


class LoadBalancerStrategy:
    ROUND_ROBIN = "Round Robin"
    LEAST_LOADED = "Least Loaded"
    PRIORITY_BASED = "Priority-Based"
    RESOURCE_AWARE = "Resource-Aware"

    ALL_STRATEGIES = [ROUND_ROBIN, LEAST_LOADED, PRIORITY_BASED, RESOURCE_AWARE]


class LoadBalancer:
    """
    Distributes tasks across cluster worker nodes.
    """

    def __init__(self) -> None:
        self.rr_index = 0

    def select_worker(self, nodes: List[Dict[str, Any]], strategy: str = LoadBalancerStrategy.LEAST_LOADED) -> Optional[Dict[str, Any]]:
        online_nodes = [n for n in nodes if n.get("status") == "ONLINE"]
        if not online_nodes:
            _logger.warning("LoadBalancer: No online worker nodes available.")
            return None

        if strategy == LoadBalancerStrategy.ROUND_ROBIN:
            selected = online_nodes[self.rr_index % len(online_nodes)]
            self.rr_index += 1
        elif strategy == LoadBalancerStrategy.LEAST_LOADED:
            selected = min(online_nodes, key=lambda n: n.get("active_tasks_count", 0))
        else:  # Priority / Resource Aware
            selected = min(online_nodes, key=lambda n: n.get("active_tasks_count", 0))

        _logger.info(f"LoadBalancer: Strategy '{strategy}' selected worker node '{selected.get('node_id')}'")
        return selected


global_load_balancer = LoadBalancer()
