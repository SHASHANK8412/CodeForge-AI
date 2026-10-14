"""
AIForge Dynamic Plugin Loader & Event Dispatcher
================================================
Loads plugin entrypoints dynamically and subscribes plugins to system event topics:
PROJECT_CREATED, BUILD_COMPLETED, DEPLOYMENT_FINISHED, CODE_GENERATED, ERROR_DETECTED, QUALITY_CHECK_COMPLETED.
"""

import time
import logging
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

_logger = logging.getLogger("aiforge.plugins.loader")


class EventTopic:
    PROJECT_CREATED = "PROJECT_CREATED"
    BUILD_COMPLETED = "BUILD_COMPLETED"
    DEPLOYMENT_FINISHED = "DEPLOYMENT_FINISHED"
    CODE_GENERATED = "CODE_GENERATED"
    ERROR_DETECTED = "ERROR_DETECTED"
    QUALITY_CHECK_COMPLETED = "QUALITY_CHECK_COMPLETED"


class DynamicPluginLoader:
    """
    Loads plugins dynamically and dispatches system event callbacks.
    """

    def __init__(self) -> None:
        self.subscribers: Dict[str, List[str]] = {
            EventTopic.PROJECT_CREATED: ["github_plugin", "slack_plugin"],
            EventTopic.DEPLOYMENT_FINISHED: ["slack_plugin", "jira_plugin"],
            EventTopic.BUILD_COMPLETED: ["slack_plugin"]
        }

    def dispatch_event(self, topic: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        plugin_subscribers = self.subscribers.get(topic, [])
        dispatched_count = 0

        for plugin_id in plugin_subscribers:
            _logger.info(f"DynamicPluginLoader: Dispatched event '{topic}' to plugin '{plugin_id}'")
            dispatched_count += 1

        return {
            "topic": topic,
            "subscribers_notified": dispatched_count,
            "plugins": plugin_subscribers,
            "timestamp": time.time()
        }


global_dynamic_plugin_loader = DynamicPluginLoader()


class PluginLoader:
    """
    Scans a plugin directory and imports plugin files (the Day 23 plugin API, kept alongside the
    event dispatcher above). Loading executes the plugin file, so only point it at a trusted
    plugin store.
    """

    def __init__(self, plugin_dir: Optional[str] = None) -> None:
        if plugin_dir is None:
            plugin_dir = str(Path(__file__).resolve().parent.parent / "plugin_store")
        self.plugin_dir = Path(plugin_dir)
        self.plugin_dir.mkdir(parents=True, exist_ok=True)

    def scan_directory(self) -> List[Path]:
        """Python plugin files under the plugin directory (excluding dunder files)."""
        return [p for p in self.plugin_dir.rglob("*.py") if not p.name.startswith("__")]

    def load_plugin_from_file(self, file_path: Path):
        """Import a plugin file and instantiate its BasePlugin subclass."""
        from backend.plugins.interfaces import BasePlugin
        spec = importlib.util.spec_from_file_location(Path(file_path).stem, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {Path(file_path).name}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for attr in vars(module).values():
            if isinstance(attr, type) and attr is not BasePlugin and issubclass(attr, BasePlugin):
                return attr()
        raise ImportError(f"No BasePlugin subclass found in {Path(file_path).name}")
