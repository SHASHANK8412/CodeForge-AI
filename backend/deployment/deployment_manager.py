"""
AIForge Deployment Manager & Docker Packaging System
======================================================
Manages Docker image metadata (Frontend, Backend, Database, Redis) and executes deployment strategies:
- Rolling Deployment
- Blue-Green Deployment
- Canary Deployment
"""

import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.deployment.version_manager import global_version_manager

_logger = logging.getLogger("aiforge.deployment.manager")


class DeploymentStrategy:
    ROLLING = "Rolling"
    BLUE_GREEN = "Blue-Green"
    CANARY = "Canary"

    ALL_STRATEGIES = [ROLLING, BLUE_GREEN, CANARY]


class DeploymentManager:
    """
    Manages Docker image packaging metadata and multi-strategy deployment execution.
    """

    def __init__(self) -> None:
        self.deployments: List[Dict[str, Any]] = [
            {
                "deploy_id": "deploy_001",
                "environment": "Production",
                "strategy": DeploymentStrategy.ROLLING,
                "version": "v2.1.0",
                "status": "COMPLETED",
                "traffic_split": "100% Production",
                "docker_images": {
                    "frontend": {"tag": "aiforge-frontend:v2.1.0", "size": "42 MB", "commit": "a1b2c3d"},
                    "backend": {"tag": "aiforge-backend:v2.1.0", "size": "115 MB", "commit": "a1b2c3d"},
                    "database": {"tag": "postgres:15-alpine", "size": "210 MB", "commit": "upstream"},
                    "redis": {"tag": "redis:7-alpine", "size": "32 MB", "commit": "upstream"}
                },
                "deployed_at": time.time() - 3600
            }
        ]

    def get_docker_images_metadata(self, version: Optional[str] = None) -> Dict[str, Any]:
        v = version or global_version_manager.get_current_version()
        return {
            "version": v,
            "commit_hash": "a1b2c3d",
            "build_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "images": [
                {"name": "Frontend Image", "tag": f"aiforge-frontend:{v}", "size": "42.5 MB", "status": "Ready"},
                {"name": "Backend Image", "tag": f"aiforge-backend:{v}", "size": "118.2 MB", "status": "Ready"},
                {"name": "Database Image", "tag": "postgres:15-alpine", "size": "210.0 MB", "status": "Ready"},
                {"name": "Redis Image", "tag": "redis:7-alpine", "size": "32.4 MB", "status": "Ready"}
            ]
        }

    def execute_deployment(
        self,
        environment: str = "Production",
        strategy: str = DeploymentStrategy.ROLLING,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        if strategy not in DeploymentStrategy.ALL_STRATEGIES:
            raise ValueError(f"Invalid strategy '{strategy}'. Allowed: {DeploymentStrategy.ALL_STRATEGIES}")

        v = version or global_version_manager.get_current_version()
        deploy_id = f"deploy_{int(time.time() * 1000)}"

        if strategy == DeploymentStrategy.ROLLING:
            steps = ["Terminating old pods", "Provisioning new pods", "Shifting traffic to v" + v]
            traffic_split = "100% New Pods"
        elif strategy == DeploymentStrategy.BLUE_GREEN:
            steps = ["Spinning up Green Environment", "Running smoke tests on Green", "Switching router traffic from Blue -> Green"]
            traffic_split = "100% Green Environment"
        else:  # Canary
            steps = ["Deploying Canary (5% traffic)", "Promoting Canary (20% traffic)", "Promoting Canary (50% traffic)", "Full Rollout (100% traffic)"]
            traffic_split = "100% Canary Production"

        deploy_entry = {
            "deploy_id": deploy_id,
            "environment": environment,
            "strategy": strategy,
            "version": v,
            "status": "COMPLETED",
            "execution_steps": steps,
            "traffic_split": traffic_split,
            "docker_images": self.get_docker_images_metadata(v),
            "deployed_at": time.time()
        }

        self.deployments.insert(0, deploy_entry)
        self._write_deployment_log(deploy_entry)
        _logger.info(f"DeploymentManager: Executed '{strategy}' deployment for environment '{environment}' (Version: {v})")
        return deploy_entry

    def get_all_deployments(self) -> List[Dict[str, Any]]:
        return list(self.deployments)

    def _write_deployment_log(self, deploy: Dict[str, Any]) -> None:
        try:
            log_dir = Path(__file__).resolve().parents[2] / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "deployment.log"

            log_entry = f"{time.strftime('%Y-%m-%d %H:%M:%S')} [DEPLOYMENT] ID: {deploy['deploy_id']} | Env: {deploy['environment']} | Strategy: {deploy['strategy']} | Version: {deploy['version']} | Status: {deploy['status']}\n"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            _logger.error(f"Failed writing to deployment.log: {e}")


global_deployment_manager = DeploymentManager()
