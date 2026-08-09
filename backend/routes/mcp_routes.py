"""
FastAPI Routes for Day 45 Model Context Protocol (MCP) Integration & Universal Tool Ecosystem
==============================================================================================
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from backend.mcp.server_registry import global_server_registry
from backend.mcp.discovery import global_mcp_discovery
from backend.mcp.mcp_manager import global_mcp_manager
from backend.mcp.health_monitor import global_mcp_health_monitor

router = APIRouter(tags=["Model Context Protocol (MCP) Ecosystem"])


class MCPExecuteRequest(BaseModel):
    server_name: str
    tool_name: str
    params: Optional[Dict[str, Any]] = None
    permission: Optional[str] = "EXECUTE"


@router.get("/api/v1/mcp/servers")
@router.get("/mcp/servers")
async def list_mcp_servers() -> Dict[str, Any]:
    """Retrieves status and metadata for all 12 registered MCP servers."""
    return {"status": "success", "servers": global_server_registry.get_all_servers()}


@router.get("/api/v1/mcp/tools")
@router.get("/mcp/tools")
async def discover_mcp_tools(server_name: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Dynamically discovers tool capabilities across active MCP servers."""
    capabilities = global_mcp_manager.discover_tools(server_name)
    return {"status": "success", "capabilities": capabilities}


@router.post("/api/v1/mcp/execute")
@router.post("/mcp/execute")
async def execute_mcp_tool(req: MCPExecuteRequest) -> Dict[str, Any]:
    """Executes dynamic MCP tool call with permission validation, retries, and offline fallback."""
    res = global_mcp_manager.execute_tool_call(
        server_name=req.server_name,
        tool_name=req.tool_name,
        params=req.params or {},
        user_permission=req.permission or "EXECUTE"
    )
    return {"status": "success", "execution_result": res}


@router.get("/api/v1/mcp/dashboard")
@router.get("/mcp/dashboard")
async def get_mcp_dashboard() -> Dict[str, Any]:
    """Retrieves live MCP Dashboard metrics: Server Health, Connection Latency, Sync Timestamps."""
    health = global_mcp_health_monitor.check_health()
    return {"status": "success", "mcp_dashboard": health}
