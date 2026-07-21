import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.plugins")

class PluginRegistry:
    """
    Manages active registry list containing plugin metadata, state toggles, and performance statistics.
    """

    def __init__(self) -> None:
        self.plugins: Dict[str, Dict[str, Any]] = {}

    def register_plugin(self, name: str, meta: Dict[str, Any]) -> None:
        name_clean = name.lower().strip()
        self.plugins[name_clean] = {
            "metadata": meta,
            "status": "Disabled",
            "metrics": {
                "invocations": 0,
                "crashes": 0,
                "execution_time_total": 0.0,
                "average_time_ms": 0.0,
                "memory_peak_kb": 0.0
            }
        }
        _logger.info(f"Registered plugin to registry: {name}")

    def update_status(self, name: str, status: str) -> None:
        name_clean = name.lower().strip()
        if name_clean in self.plugins:
            self.plugins[name_clean]["status"] = status
            _logger.info(f"Updated status of '{name}' to: {status}")

    def get_plugin(self, name: str) -> Dict[str, Any]:
        return self.plugins.get(name.lower().strip(), {})

    def get_all_registered(self) -> Dict[str, Dict[str, Any]]:
        return self.plugins

    def unregister_plugin(self, name: str) -> None:
        name_clean = name.lower().strip()
        if name_clean in self.plugins:
            del self.plugins[name_clean]
            _logger.info(f"Unregistered plugin from registry: {name}")
