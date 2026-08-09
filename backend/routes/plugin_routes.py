"""
FastAPI Routes for Day 39 AI Plugin Ecosystem & Tool Marketplace
=================================================================
Exposes REST APIs for plugin installation, uninstallation, updates, activation/deactivation, marketplace browsing, and plugin dashboards.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from backend.plugins.manager import global_plugin_manager
from backend.plugins.registry import global_plugin_registry
from backend.plugins.marketplace import global_plugin_marketplace
from backend.plugins.loader import global_dynamic_plugin_loader

router = APIRouter(tags=["AI Plugin Ecosystem & Marketplace"])


class InstallPluginInput(BaseModel):
    name: str
    version: Optional[str] = "1.0.0"
    author: Optional[str] = "AIForge Core"
    description: Optional[str] = ""
    permissions: Optional[List[str]] = []
    entry: Optional[str] = "plugin.py"


class UpdatePluginInput(BaseModel):
    plugin_id: str
    new_version: Optional[str] = "1.1.0"


class PluginActionInput(BaseModel):
    plugin_id: str


@router.get("/plugins")
@router.get("/api/v1/plugins")
async def list_plugins(status: Optional[str] = Query(None, description="Filter by status: ACTIVE, DISABLED")) -> Dict[str, Any]:
    """Retrieves all installed plugins and their statuses."""
    plugins = global_plugin_registry.list_plugins(status=status)
    return {"status": "success", "total_plugins": len(plugins), "plugins": plugins}


@router.get("/plugins/marketplace")
@router.get("/api/v1/plugins/marketplace")
async def get_plugin_marketplace(category: Optional[str] = Query(None, description="Filter by category")) -> Dict[str, Any]:
    """Retrieves Plugin Marketplace catalog, ratings, and download metrics."""
    catalog = global_plugin_marketplace.get_marketplace_catalog(category=category)
    return {"status": "success", "marketplace": catalog}


@router.get("/plugins/{plugin_id}")
@router.get("/api/v1/plugins/{plugin_id}")
async def get_plugin_details(plugin_id: str) -> Dict[str, Any]:
    """Retrieves details and manifest metadata for a specific plugin."""
    plugin = global_plugin_registry.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_id}' not found.")
    return {"status": "success", "plugin": plugin}


@router.post("/plugins/install")
@router.post("/api/v1/plugins/install")
async def install_plugin(req: InstallPluginInput) -> Dict[str, Any]:
    """Validates manifest, verifies permissions, and installs a new plugin dynamically."""
    try:
        manifest = req.dict()
        res = global_plugin_manager.install_plugin(manifest)
        return {"status": "success", "installation_result": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/plugins/uninstall")
@router.post("/api/v1/plugins/uninstall")
async def uninstall_plugin(req: PluginActionInput) -> Dict[str, Any]:
    """Uninstalls a plugin from the platform."""
    try:
        res = global_plugin_manager.uninstall_plugin(req.plugin_id)
        return {"status": "success", "uninstall_result": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/plugins/enable")
@router.post("/api/v1/plugins/enable")
async def enable_plugin(req: PluginActionInput) -> Dict[str, Any]:
    """Activates an installed plugin."""
    try:
        res = global_plugin_manager.enable_plugin(req.plugin_id)
        return {"status": "success", "enable_result": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/plugins/disable")
@router.post("/api/v1/plugins/disable")
async def disable_plugin(req: PluginActionInput) -> Dict[str, Any]:
    """Deactivates an active plugin."""
    try:
        res = global_plugin_manager.disable_plugin(req.plugin_id)
        return {"status": "success", "disable_result": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/plugins/update")
@router.post("/api/v1/plugins/update")
async def update_plugin(req: UpdatePluginInput) -> Dict[str, Any]:
    """Upgrades an installed plugin version."""
    try:
        res = global_plugin_manager.update_plugin(req.plugin_id, req.new_version or "1.1.0")
        return {"status": "success", "update_result": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/plugins/dashboard")
@router.get("/api/v1/plugins/dashboard")
async def get_plugin_dashboard() -> Dict[str, Any]:
    """Retrieves Plugin Dashboard data: Installed Plugins, Plugin Status, Versions, Resource Usage, Permissions, Event Subscriptions."""
    dash = global_plugin_manager.get_plugin_dashboard()
    return {"status": "success", "plugin_dashboard": dash}
