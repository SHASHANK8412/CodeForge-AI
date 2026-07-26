import logging
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.plugins.manager import global_plugin_manager

logger = logging.getLogger("aiforge.routes.plugins")

router = APIRouter(tags=["Autonomous Plugin System & Tool Framework"])


class InstallPluginRequest(BaseModel):
    name: str = Field(min_length=1)
    version: str = "1.0.0"
    permissions: List[str] = Field(default_factory=list)


class TogglePluginRequest(BaseModel):
    plugin_id: str = Field(min_length=1)


class ExecuteToolRequest(BaseModel):
    plugin_id: str = Field(min_length=1)
    params: Dict[str, Any] = Field(default_factory=dict)


@router.get("/plugins")
@router.get("/api/plugins")
def list_plugins():
    """Lists all installed plugins and execution metrics."""
    return {"plugins": global_plugin_manager.list_all_plugins()}


@router.post("/plugins/install")
@router.post("/api/plugins/install")
def install_plugin(req: InstallPluginRequest):
    """Installs a new plugin SDK module."""
    return global_plugin_manager.install_plugin(req.name, req.version, req.permissions)


@router.post("/plugins/enable")
@router.post("/api/plugins/enable")
def enable_plugin(req: TogglePluginRequest):
    """Enables an installed plugin."""
    success = global_plugin_manager.enable_plugin(req.plugin_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Plugin '{req.plugin_id}' not found.")
    return {"status": "success", "message": f"Plugin '{req.plugin_id}' enabled."}


@router.post("/plugins/disable")
@router.post("/api/plugins/disable")
def disable_plugin(req: TogglePluginRequest):
    """Disables an installed plugin."""
    success = global_plugin_manager.disable_plugin(req.plugin_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Plugin '{req.plugin_id}' not found.")
    return {"status": "success", "message": f"Plugin '{req.plugin_id}' disabled."}


@router.post("/plugins/execute")
@router.post("/api/plugins/execute")
def execute_plugin(req: ExecuteToolRequest):
    """Executes a plugin tool safely via ToolExecutionEngine."""
    return global_plugin_manager.execute_plugin(req.plugin_id, req.params)


@router.get("/plugins/logs")
@router.get("/api/plugins/logs")
def get_plugin_logs(limit: int = Query(50, ge=1, le=200)):
    """Returns recent tool execution telemetry logs."""
    return {"logs": global_plugin_manager.get_logs(limit)}
