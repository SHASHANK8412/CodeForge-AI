import importlib.util
import logging
from pathlib import Path
from typing import Dict, Any, List

from backend.plugins.interfaces import BasePlugin

_logger = logging.getLogger("aiforge.plugins")

class PluginLoader:
    """
    Handles scanning and runtime hot-reloading imports of plugins.
    """

    def __init__(self, plugin_dir: str = None) -> None:
        if plugin_dir is None:
            plugin_dir = str(Path(__file__).resolve().parent.parent / "plugin_store")
        self.plugin_dir = Path(plugin_dir)
        self.plugin_dir.mkdir(parents=True, exist_ok=True)

    def load_plugin_from_file(self, file_path: Path) -> BasePlugin:
        """
        Dynamically imports a Python file and returns the BasePlugin implementation.
        """
        try:
            module_name = file_path.stem
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load spec for {file_path.name}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find BasePlugin subclass
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and attr is not BasePlugin and issubclass(attr, BasePlugin):
                    # Found subclass! Instantiate
                    plugin_instance = attr()
                    return plugin_instance
            
            raise ImportError(f"No BasePlugin subclass found in {file_path.name}")
        except Exception as e:
            _logger.error(f"Failed to dynamically load plugin file {file_path.name}: {str(e)}")
            raise e

    def scan_directory(self) -> List[Path]:
        """
        Recursively scans plugin directory searching for Python plugin files.
        """
        # Find all python files not starting with double underscore
        return [p for p in self.plugin_dir.rglob("*.py") if not p.name.startswith("__")]
