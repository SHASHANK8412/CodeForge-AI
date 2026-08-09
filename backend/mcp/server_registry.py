"""
AIForge MCP Server Registry (Day 45)
=====================================
Maintains status, endpoint URIs, and capabilities for 12 supported Model Context Protocol (MCP) servers.
"""

import time
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.mcp.server_registry")


class ServerRegistry:
    """
    Registry managing availability status, latency, and endpoints for 12 supported MCP servers.
    """

    def __init__(self):
        self.servers: Dict[str, Dict[str, Any]] = {
            "filesystem": {"name": "filesystem", "status": "connected", "latency_ms": 12, "version": "1.2.0", "uri": "mcp://filesystem.local"},
            "github": {"name": "github", "status": "connected", "latency_ms": 145, "version": "2.1.0", "uri": "mcp://api.github.com/mcp"},
            "postgres": {"name": "postgres", "status": "connected", "latency_ms": 24, "version": "1.0.4", "uri": "mcp://localhost:5432/mcp"},
            "docker": {"name": "docker", "status": "connected", "latency_ms": 35, "version": "2.0.1", "uri": "mcp://docker.sock"},
            "browser": {"name": "browser", "status": "connected", "latency_ms": 180, "version": "1.1.0", "uri": "mcp://localhost:9222/mcp"},
            "terminal": {"name": "terminal", "status": "connected", "latency_ms": 8, "version": "1.0.0", "uri": "mcp://sandbox.terminal"},
            "redis": {"name": "redis", "status": "connected", "latency_ms": 5, "version": "1.0.1", "uri": "mcp://localhost:6379"},
            "kubernetes": {"name": "kubernetes", "status": "connected", "latency_ms": 65, "version": "1.28.0", "uri": "mcp://k8s.local"},
            "aws": {"name": "aws", "status": "connected", "latency_ms": 210, "version": "2.4.0", "uri": "mcp://aws.amazon.com/mcp"},
            "slack": {"name": "slack", "status": "offline", "latency_ms": 0, "version": "1.0.0", "uri": "mcp://slack.com/mcp"},
            "jira": {"name": "jira", "status": "connected", "latency_ms": 195, "version": "1.3.0", "uri": "mcp://atlassian.net/mcp"},
            "notion": {"name": "notion", "status": "connected", "latency_ms": 160, "version": "1.0.0", "uri": "mcp://notion.so/mcp"}
        }

    def get_server_status(self, server_name: str) -> Optional[Dict[str, Any]]:
        return self.servers.get(server_name)

    def set_server_status(self, server_name: str, status: str, latency_ms: int = 0) -> bool:
        if server_name in self.servers:
            self.servers[server_name]["status"] = status
            self.servers[server_name]["latency_ms"] = latency_ms
            _logger.info(f"ServerRegistry: Updated MCP Server '{server_name}' -> status: '{status}'")
            return True
        return False

    def get_all_servers(self) -> Dict[str, Dict[str, Any]]:
        return self.servers

    def get_connected_servers(self) -> List[str]:
        return [name for name, s in self.servers.items() if s.get("status") == "connected"]


global_server_registry = ServerRegistry()
