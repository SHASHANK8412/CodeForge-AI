import pytest
from pathlib import Path
from backend.plugins.manager import PluginManager

class MockSamplePlugin:
    @property
    def name(self) -> str:
        return "Sample"
    @property
    def version(self) -> str:
        return "1.0.0"
    @property
    def author(self) -> str:
        return "Author"
    @property
    def description(self) -> str:
        return "Description"
    @property
    def permissions(self) -> list:
        return ["filesystem:read"]
    @property
    def dependencies(self) -> list:
        return []
    def initialize(self):
        pass
    def execute(self, ctx):
        ctx["status"] = "Executed"
        return ctx
    def validate(self):
        return True
    def shutdown(self):
        pass
    def before_execute(self, ctx):
        return ctx
    def after_execute(self, res):
        return res
    def rollback(self, ctx):
        pass
    def serialize(self):
        return {"name": self.name, "version": self.version, "permissions": self.permissions, "dependencies": self.dependencies}

def test_plugin_lifecycle():
    manager = PluginManager()
    
    # Register mock plugin directly
    plugin = MockSamplePlugin()
    manager.loaded_instances["sample"] = plugin
    manager.registry.register_plugin(plugin.name, plugin.serialize())

    # Try executing disabled plugin (should fail)
    with pytest.raises(ValueError, match="is not currently active"):
        manager.execute_plugin("Sample", {})

    # Enable and execute
    manager.enable_plugin("Sample")
    res = manager.execute_plugin("Sample", {"input": 42})
    assert res["status"] == "Executed"
    assert res["input"] == 42
