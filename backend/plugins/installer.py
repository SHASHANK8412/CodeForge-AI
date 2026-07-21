import shutil
import logging
from pathlib import Path
from typing import Dict, Any

_logger = logging.getLogger("aiforge.plugins")

class PluginInstaller:
    """
    Simulates downloading, upgrading, and installing plugin packages to the local plugin store.
    """

    def __init__(self, plugin_dir: str = None) -> None:
        if plugin_dir is None:
            plugin_dir = str(Path(__file__).resolve().parent.parent / "plugin_store")
        self.plugin_dir = Path(plugin_dir)

    def install_plugin_from_source(self, name: str, source_code: str) -> Path:
        """
        Installs a plugin by writing the raw code directly to the plugin store.
        """
        # Save under namespace custom or directly
        target_dir = self.plugin_dir / "custom"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = target_dir / f"{name.lower()}_plugin.py"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(source_code)
            _logger.info(f"Successfully installed plugin source to: {file_path.name}")
            return file_path
        except Exception as e:
            _logger.error(f"Failed to install plugin {name}: {str(e)}")
            raise e

    def uninstall_plugin(self, name: str) -> bool:
        """
        Removes plugin file from local plugin store.
        """
        target_file = self.plugin_dir / "custom" / f"{name.lower()}_plugin.py"
        if target_file.exists():
            try:
                target_file.unlink()
                _logger.info(f"Uninstalled plugin successfully: {target_file.name}")
                return True
            except Exception as e:
                _logger.error(f"Failed to unlink plugin file: {str(e)}")
                return False
        return False
