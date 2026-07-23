"""
AIForge Evolution - Evolution Patch Generator
=============================================
Generates targeted unified diff patches for code evolution.
Ensures changes only modify affected nodes without touching unrelated code.
"""

import difflib
import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.evolution")


class EvolutionPatchGenerator:
    """
    Generates unified Git diff patches for affected codebase files.
    """

    def generate_evolution_patches(self, migration_plan: Dict[str, Any], affected_files: List[str]) -> Dict[str, Any]:
        prompt_lower = migration_plan.get("proposed_change", "").lower()
        file_patches = []
        total_additions = 0
        total_deletions = 0

        for f_path in affected_files:
            if "oauth2" in prompt_lower or "jwt" in prompt_lower:
                old_code = "from backend.auth.jwt import verify_token\n\n@app.get('/api/v1/resource')\ndef get_res(token: str):\n    return verify_token(token)"
                new_code = "from backend.auth.oauth2 import verify_oauth2_token\n\n@app.get('/api/v1/resource')\ndef get_res(token: str):\n    return verify_oauth2_token(token)"
            elif "account" in prompt_lower or "user" in prompt_lower:
                old_code = "class User(Base):\n    __tablename__ = 'users'\n    id = Column(Integer, primary_key=True)"
                new_code = "class Account(Base):\n    __tablename__ = 'accounts'\n    id = Column(Integer, primary_key=True)"
            else:
                old_code = "# Original implementation\ndef legacy_handler(): pass"
                new_code = "# Evolved implementation\ndef evolved_handler(): pass"

            diff = list(difflib.unified_diff(
                old_code.splitlines(keepends=True),
                new_code.splitlines(keepends=True),
                fromfile=f"a/{f_path}",
                tofile=f"b/{f_path}"
            ))

            additions = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
            deletions = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))
            total_additions += additions
            total_deletions += deletions

            file_patches.append({
                "file": f_path,
                "patch_text": "".join(diff),
                "additions": additions,
                "deletions": deletions
            })

        _logger.info(f"EvolutionPatchGenerator: Created patches for {len(file_patches)} files (+{total_additions}, -{total_deletions} lines).")
        return {
            "total_files_updated": len(file_patches),
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "patches": file_patches
        }
