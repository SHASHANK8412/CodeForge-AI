"""
AIForge Plugin Marketplace
==========================
Marketplace catalog featuring top plugins, ratings, download metrics, categories, and update notifications.
"""

import logging
from typing import Dict, Any, List, Optional
from backend.plugins.registry import global_plugin_registry

_logger = logging.getLogger("aiforge.plugins.marketplace")


class PluginMarketplace:
    """
    Plugin Marketplace catalog.
    """

    def __init__(self) -> None:
        self.catalog: List[Dict[str, Any]] = [
            {
                "id": "github_plugin",
                "name": "GitHub Integration Plugin",
                "version": "1.0.0",
                "author": "AIForge Core",
                "rating": 4.9,
                "downloads": 14200,
                "category": "Integrations",
                "description": "Full GitHub Repository, Pull Request, and Actions automation."
            },
            {
                "id": "slack_plugin",
                "name": "Slack Alert Dispatcher",
                "version": "1.2.0",
                "author": "AIForge Core",
                "rating": 4.8,
                "downloads": 9800,
                "category": "Productivity",
                "description": "Dispatches project progress and build alerts directly to Slack."
            },
            {
                "id": "jira_plugin",
                "name": "Jira Task Sync Plugin",
                "version": "2.0.1",
                "author": "Atlassian Partner",
                "rating": 4.7,
                "downloads": 8400,
                "category": "Productivity",
                "description": "Synchronizes AIForge sprint tasks automatically with Jira tickets."
            },
            {
                "id": "docker_plugin",
                "name": "Docker Container Security Auditor",
                "version": "1.1.0",
                "author": "DevOps Security Team",
                "rating": 4.9,
                "downloads": 11500,
                "category": "DevOps",
                "description": "Audits Dockerfile base images for CVE security vulnerabilities."
            }
        ]

    def get_marketplace_catalog(self, category: Optional[str] = None) -> Dict[str, Any]:
        results = self.catalog
        if category:
            results = [p for p in results if p["category"].lower() == category.lower()]
        
        installed = global_plugin_registry.list_plugins()
        installed_ids = [p["id"] for p in installed]

        return {
            "categories": ["AI Agents", "Productivity", "DevOps", "Cloud", "Security", "Documentation", "Analytics"],
            "total_marketplace_plugins": len(results),
            "plugins": results,
            "installed_plugin_ids": installed_ids
        }


global_plugin_marketplace = PluginMarketplace()
