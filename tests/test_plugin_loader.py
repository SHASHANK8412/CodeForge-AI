import pytest
from pathlib import Path
from backend.plugins.loader import PluginLoader

def test_plugin_loader_scanning(tmp_path):
    # Setup mock files
    custom_dir = tmp_path / "custom"
    custom_dir.mkdir(parents=True, exist_ok=True)
    
    p1 = custom_dir / "test1_plugin.py"
    p1.write_text("class MyPlugin: pass")
    
    loader = PluginLoader(plugin_dir=str(tmp_path))
    files = loader.scan_directory()
    assert len(files) == 1
    assert files[0].name == "test1_plugin.py"
