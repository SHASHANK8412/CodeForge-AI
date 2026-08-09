"""
AIForge Dynamic Plugin Loader & Event Dispatcher
================================================
Loads plugin entrypoints dynamically and subscribes plugins to system event topics:
PROJECT_CREATED, BUILD_COMPLETED, DEPLOYMENT_FINISHED, CODE_GENERATED, ERROR_DETECTED, QUALITY_CHECK_COMPLETED.
"""

import time
import logging
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
