"""
AIForge MCP (Model Context Protocol) Gateway
============================================
Universal Tool, Resource, and Prompt standard based on the Model Context Protocol (MCP).
Standardizes how autonomous specialist agents discover and invoke tools in isolated sandboxes
with granular permissions, capability negotiation, and human approval gateways.
"""

import time
import uuid
import json
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field

_logger = logging.getLogger("aiforge.mcp.gateway")


class MCPToolRiskLevel(str, Enum):
    READ_ONLY = "READ_ONLY"      # e.g., inspect_file, list_dir, query_db (Auto-approved)
    COMPUTE = "COMPUTE"          # e.g., run_tests, run_linter (Auto-approved in sandbox)
    DESTRUCTIVE = "DESTRUCTIVE"  # e.g., write_file, execute_shell, deploy (Requires Human Approval)


class MCPToolDefinition(BaseModel):
    name: str
    server_id: str
    description: str
    input_schema: Dict[str, Any]
    risk_level: MCPToolRiskLevel = MCPToolRiskLevel.READ_ONLY
    requires_approval: bool = False
    enabled: bool = True


class MCPServerDefinition(BaseModel):
    id: str
    name: str
    version: str = "1.0.0"
    transport: str = "HTTP_SSE"  # "HTTP_SSE", "STDIO"
    description: str
    status: str = "CONNECTED"
    tools_count: int = 0
    capabilities: List[str] = Field(default_factory=lambda: ["tools", "resources", "prompts"])


# Built-in MCP Servers conforming to MCP specification
BUILTIN_MCP_SERVERS = [
    {
        "id": "mcp-server-filesystem",
        "name": "Sandbox Filesystem MCP Server",
        "description": "Secure file inspection, AST parsing, and atomic diff-based file mutations.",
        "transport": "HTTP_SSE",
        "status": "CONNECTED",
        "tools_count": 4
    },
    {
        "id": "mcp-server-shell",
        "name": "Sandbox Shell & Test Runner MCP Server",
        "description": "Isolated container shell for running test suites (pytest, jest), linters, and compilers.",
        "transport": "HTTP_SSE",
        "status": "CONNECTED",
        "tools_count": 3
    },
    {
        "id": "mcp-server-visual-qa",
        "name": "Visual QA & DOM Inspector MCP Server",
        "description": "Headless browser automation for UI visual regression, layout audit, and screenshot diffing.",
        "transport": "HTTP_SSE",
        "status": "CONNECTED",
        "tools_count": 3
    },
    {
        "id": "mcp-server-memory",
        "name": "AIForge Memory & Graph MCP Server",
        "description": "Semantic recall and architectural constraint verification across user & project memory.",
        "transport": "HTTP_SSE",
        "status": "CONNECTED",
        "tools_count": 2
    },
    {
        "id": "mcp-server-git",
        "name": "Git Version Control MCP Server",
        "description": "Branching, commit history analysis, and pull request change-set synthesis.",
        "transport": "HTTP_SSE",
        "status": "CONNECTED",
        "tools_count": 3
    }
]

BUILTIN_MCP_TOOLS = [
    {
        "name": "filesystem.read_file",
        "server_id": "mcp-server-filesystem",
        "description": "Reads file contents safely from project workspace sandbox.",
        "risk_level": "READ_ONLY",
        "requires_approval": False,
        "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
    },
    {
        "name": "filesystem.write_file_patch",
        "server_id": "mcp-server-filesystem",
        "description": "Applies verified patch/diff to project files. (Requires Human Consent).",
        "risk_level": "DESTRUCTIVE",
        "requires_approval": True,
        "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "diff": {"type": "string"}}, "required": ["path", "diff"]}
    },
    {
        "name": "shell.run_test_suite",
        "server_id": "mcp-server-shell",
        "description": "Executes pytest or npm test in isolated sandbox and captures stacktrace.",
        "risk_level": "COMPUTE",
        "requires_approval": False,
        "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}
    },
    {
        "name": "visual_qa.audit_ui_layout",
        "server_id": "mcp-server-visual-qa",
        "description": "Performs automated accessibility, contrast, and visual alignment audit on rendered components.",
        "risk_level": "READ_ONLY",
        "requires_approval": False,
        "input_schema": {"type": "object", "properties": {"component": {"type": "string"}}, "required": ["component"]}
    },
    {
        "name": "git.create_feature_branch",
        "server_id": "mcp-server-git",
        "description": "Creates an isolated git feature branch for autonomous agent modifications.",
        "risk_level": "COMPUTE",
        "requires_approval": False,
        "input_schema": {"type": "object", "properties": {"branch_name": {"type": "string"}}, "required": ["branch_name"]}
    }
]


class MCPGateway:
    def __init__(self):
        self._servers: Dict[str, MCPServerDefinition] = {}
        self._tools: Dict[str, MCPToolDefinition] = {}
        self._init_builtins()

    def _init_builtins(self):
        for s in BUILTIN_MCP_SERVERS:
            self._servers[s["id"]] = MCPServerDefinition(**s)
        for t in BUILTIN_MCP_TOOLS:
            self._tools[t["name"]] = MCPToolDefinition(**t)

    def list_servers(self) -> List[MCPServerDefinition]:
        return list(self._servers.values())

    def list_tools(self, server_id: Optional[str] = None) -> List[MCPToolDefinition]:
        tools = list(self._tools.values())
        if server_id:
            tools = [t for t in tools if t.server_id == server_id]
        return tools

    def invoke_tool(self, tool_name: str, arguments: Dict[str, Any], user_approved: bool = False) -> Dict[str, Any]:
        tool = self._tools.get(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool '{tool_name}' not registered in MCP Gateway"}

        if tool.requires_approval and not user_approved:
            return {
                "success": False,
                "status": "WAITING_APPROVAL",
                "tool": tool_name,
                "risk_level": tool.risk_level.value,
                "reason": f"Tool '{tool_name}' modifies project state and requires human approval."
            }

        # Simulated tool execution in Sandbox
        _logger.info(f"MCP Gateway executing {tool_name} with args: {arguments}")
        return {
            "success": True,
            "status": "COMPLETED",
            "tool": tool_name,
            "output": f"Successfully executed {tool_name} in isolated sandbox runtime.",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }


global_mcp_gateway = MCPGateway()
