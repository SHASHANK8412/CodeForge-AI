import pytest
from backend.plugins.installer import PluginInstaller

def test_installation_routines(tmp_path):
    installer = PluginInstaller(plugin_dir=str(tmp_path))
    
    source = "class PostgresPlugin: pass"
    file_path = installer.install_plugin_from_source("postgres", source)
    assert file_path.exists()

    uninstalled = installer.uninstall_plugin("postgres")
    assert uninstalled is True
    assert not file_path.exists()
