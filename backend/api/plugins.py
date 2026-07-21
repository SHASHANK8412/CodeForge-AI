import logging
from fastapi import APIRouter, HTTPException, Query, Body
from typing import Dict, Any, List

from backend.plugins.manager import PluginManager

router = APIRouter(prefix="/plugins", tags=["Plugins"])

# Shared global manager (for simplicity, uses default store path)
manager = PluginManager()
manager.discover_and_load_plugins()

@router.get("")
def list_plugins() -> Dict[str, Dict[str, Any]]:
    """
    Returns lists of all scanned registered plugins.
    """
    return manager.registry.get_all_registered()

@router.get("/{name}")
def get_plugin_details(name: str) -> Dict[str, Any]:
    info = manager.registry.get_plugin(name)
    if not info:
        raise HTTPException(status_code=404, detail="Plugin not found")
    # Tally real-time metrics
    info["metrics"] = manager.monitor.get_metrics_for_plugin(name)
    return info

@router.post("/enable")
def enable_plugin(name: str = Query(...)) -> Dict[str, Any]:
    success = manager.enable_plugin(name)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to enable plugin")
    return {"status": "Success", "message": f"Plugin '{name}' enabled successfully."}

@router.post("/disable")
def disable_plugin(name: str = Query(...)) -> Dict[str, Any]:
    success = manager.disable_plugin(name)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to disable plugin")
    return {"status": "Success", "message": f"Plugin '{name}' disabled successfully."}

@router.post("/install")
def install_plugin(
    name: str = Body(..., embed=True),
    source_code: str = Body(..., embed=True)
) -> Dict[str, Any]:
    success = manager.install_plugin(name, source_code)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to install plugin source")
    return {"status": "Success", "message": f"Plugin '{name}' installed and registered."}

@router.post("/uninstall")
def uninstall_plugin(name: str = Query(...)) -> Dict[str, Any]:
    success = manager.uninstall_plugin(name)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to uninstall plugin")
    return {"status": "Success", "message": f"Plugin '{name}' uninstalled."}

@router.get("/metrics/{name}")
def get_plugin_metrics(name: str) -> Dict[str, Any]:
    return manager.monitor.get_metrics_for_plugin(name)
