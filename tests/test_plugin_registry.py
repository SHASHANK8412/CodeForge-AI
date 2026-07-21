import pytest
from backend.plugins.registry import PluginRegistry

def test_registry_lifecycle():
    registry = PluginRegistry()
    meta = {"name": "TestPlugin", "version": "1.0.0"}
    
    registry.register_plugin("TestPlugin", meta)
    assert registry.get_plugin("TestPlugin")["status"] == "Disabled"

    registry.update_status("TestPlugin", "Active")
    assert registry.get_plugin("TestPlugin")["status"] == "Active"

    registry.unregister_plugin("TestPlugin")
    assert registry.get_plugin("TestPlugin") == {}
