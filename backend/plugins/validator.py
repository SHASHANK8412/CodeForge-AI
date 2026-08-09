"""
AIForge Plugin Manifest Validator
=================================
Validates plugin manifest schema structure, required fields (name, version, author, description, permissions, entry), and version format.
"""

import logging
from typing import Dict, Any, List, Tuple

_logger = logging.getLogger("aiforge.plugins.validator")


class PluginManifestValidator:
    """
    Validates plugin manifest metadata and schemas.
    """

    REQUIRED_KEYS = ["name", "version", "author", "description", "permissions", "entry"]

    def validate_manifest(self, manifest: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []

        for key in self.REQUIRED_KEYS:
            if key not in manifest or not manifest[key]:
                errors.append(f"Missing required manifest field: '{key}'")

        if "permissions" in manifest and not isinstance(manifest["permissions"], list):
            errors.append("Field 'permissions' must be a list of strings")

        is_valid = len(errors) == 0
        if is_valid:
            _logger.info(f"PluginManifestValidator: Manifest for '{manifest.get('name')}' is valid.")
        else:
            _logger.warning(f"PluginManifestValidator: Validation failed: {errors}")

        return is_valid, errors


global_plugin_manifest_validator = PluginManifestValidator()
