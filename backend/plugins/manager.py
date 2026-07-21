import logging
from pathlib import Path
from typing import Dict, Any, List

from backend.plugins.registry import PluginRegistry
from backend.plugins.loader import PluginLoader
from backend.plugins.installer import PluginInstaller
from backend.plugins.monitor import PluginMonitor
from backend.plugins.events import PluginEventBus
from backend.plugins.sandbox import PluginSandbox, SandboxException
from backend.plugins.interfaces import BasePlugin

_logger = logging.getLogger("aiforge.plugins")

class PluginManager:
    """
    Core orchestrator coordinating dynamic loading, sandboxing, monitoring, and installation lifecycles.
    """

    def __init__(self, plugin_dir: str = None) -> None:
        self.registry = PluginRegistry()
        self.loader = PluginLoader(plugin_dir)
        self.installer = PluginInstaller(plugin_dir)
        self.monitor = PluginMonitor()
        self.event_bus = PluginEventBus()
        
        # Instantiate active running plugin objects
        self.loaded_instances: Dict[str, BasePlugin] = {}

    def discover_and_load_plugins(self) -> None:
        """
        Scans local plugin directories and registers valid plugin metadata.
        """
        _logger.info("Scanning for plugins...")
        files = self.loader.scan_directory()
        
        for f in files:
            try:
                plugin = self.loader.load_plugin_from_file(f)
                name_clean = plugin.name.lower().strip()
                
                # Check duplicate registry
                if name_clean in self.loaded_instances:
                    continue
                
                self.loaded_instances[name_clean] = plugin
                self.registry.register_plugin(plugin.name, plugin.serialize())
                
                # Default status is disabled, enable manually
                self.event_bus.publish("PluginLoaded", plugin.name)
            except Exception as e:
                _logger.error(f"Skipping corrupt or invalid plugin file {f.name}: {str(e)}")

    def enable_plugin(self, name: str) -> bool:
        """
        Activates a registered plugin. Runs its initialize method.
        """
        name_clean = name.lower().strip()
        plugin = self.loaded_instances.get(name_clean)
        
        if not plugin:
            _logger.warning(f"Cannot enable plugin '{name}': Not loaded.")
            return False

        try:
            plugin.initialize()
            self.registry.update_status(plugin.name, "Active")
            self.event_bus.publish("PluginActivated", plugin.name)
            return True
        except Exception as e:
            _logger.error(f"Failed to enable SRE plugin {plugin.name}: {str(e)}")
            return False

    def disable_plugin(self, name: str) -> bool:
        """
        Disables a registered plugin. Runs shutdown hooks.
        """
        name_clean = name.lower().strip()
        plugin = self.loaded_instances.get(name_clean)
        
        if not plugin:
            _logger.warning(f"Cannot disable plugin '{name}': Not loaded.")
            return False

        try:
            plugin.shutdown()
            self.registry.update_status(plugin.name, "Disabled")
            self.event_bus.publish("PluginDisabled", plugin.name)
            return True
        except Exception as e:
            _logger.error(f"Failed to disable SRE plugin {plugin.name}: {str(e)}")
            return False

    def execute_plugin(self, name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs plugin execute method securely in the sandbox.
        """
        name_clean = name.lower().strip()
        plugin = self.loaded_instances.get(name_clean)
        
        if not plugin:
            raise ValueError(f"Plugin '{name}' not found or not active.")

        reg_info = self.registry.get_plugin(name_clean)
        if reg_info.get("status") != "Active":
            raise ValueError(f"Plugin '{name}' is not currently active.")

        # Create sandbox context with permissions mapping
        sandbox = PluginSandbox(allowed_permissions=plugin.permissions)
        
        start = self.monitor.start_invocation(plugin.name)
        success = False
        
        try:
            # Lifecycle pre-hook
            context = plugin.before_execute(context)
            
            # Secure execute
            result = sandbox.execute_safely(
                func=plugin.execute,
                context=context,
                required_perms=plugin.permissions
            )
            
            # Lifecycle post-hook
            result = plugin.after_execute(result)
            
            success = True
            self.event_bus.publish("PluginExecuted", plugin.name)
            return result
        except Exception as e:
            self.event_bus.publish("PluginFailed", plugin.name)
            plugin.rollback(context)
            raise e
        finally:
            self.monitor.record_metrics(plugin.name, start, success)

    def install_plugin(self, name: str, source_code: str) -> bool:
        """
        Saves plugin to store directory and runs reload.
        """
        try:
            file_path = self.installer.install_plugin_from_source(name, source_code)
            self.discover_and_load_plugins()
            self.event_bus.publish("PluginInstalled", name)
            return True
        except Exception as e:
            _logger.error(f"Failed to dynamically install SRE plugin: {str(e)}")
            return False

    def uninstall_plugin(self, name: str) -> bool:
        """
        Unloads plugin from registry and deletes local package file.
        """
        name_clean = name.lower().strip()
        if name_clean in self.loaded_instances:
            self.disable_plugin(name)
            del self.loaded_instances[name_clean]
            self.registry.unregister_plugin(name)
            self.installer.uninstall_plugin(name)
            self.event_bus.publish("PluginRemoved", name)
            return True
        return False
