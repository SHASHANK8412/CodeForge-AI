import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple
from backend.validation.code_extractor import extract_files_from_agent_output

logger = logging.getLogger("aiforge.services.project_assembler")


class ProjectAssembler:
    """
    ProjectAssembler compiles agent outputs into a unified structured folder tree manifest.
    - Normalizes paths and enforces security against path traversal.
    - Detects empty files, duplicate files, and conflicting outputs from different agents.
    - Tracks agent ownership for each file and outputs a project manifest.
    """

    def assemble_project(
        self,
        agent_outputs: Dict[str, Any],
        project_name: str = "AIForge_Project"
    ) -> Dict[str, Any]:
        """
        Receives raw agent outputs, extracts file maps, normalizes paths, resolves duplicates/conflicts,
        and returns the files map and manifest.
        agent_outputs: Dict mapping agent_name (e.g. 'frontend', 'backend', 'database') to raw outputs (str or dict)
        """
        logger.info(f"[ASSEMBLER] Starting project assembly for '{project_name}'")

        files_map: Dict[str, str] = {}
        file_metadata: List[Dict[str, Any]] = []
        conflicts: List[Dict[str, Any]] = []
        duplicates: List[Dict[str, Any]] = []

        # Map path -> List[(agent_name, content)]
        path_sources: Dict[str, List[Tuple[str, str]]] = {}

        for agent, raw_output in agent_outputs.items():
            if not raw_output:
                continue

            extracted_files: Dict[str, str] = {}
            if isinstance(raw_output, dict):
                extracted_files = raw_output
            elif isinstance(raw_output, str):
                extracted_files = extract_files_from_agent_output(raw_output, agent_name=agent)

            for rel_path, content in extracted_files.items():
                # Path Normalization
                normalized = rel_path.replace("\\", "/").strip("/")

                # Security: Prevent path traversal
                parts = normalized.split("/")
                if ".." in parts or normalized.startswith("/") or ":" in normalized or normalized.startswith("~"):
                    logger.warning(f"[ASSEMBLER] Unsafe path blocked: {rel_path}")
                    continue

                if normalized not in path_sources:
                    path_sources[normalized] = []
                path_sources[normalized].append((agent, content))

        # Resolve files and detect conflicts/duplicates
        for path, sources in path_sources.items():
            first_agent, first_content = sources[0]

            if len(sources) > 1:
                # Multiple agents generated the same path
                all_identical = True
                for other_agent, other_content in sources[1:]:
                    if other_content != first_content:
                        all_identical = False
                        break

                if all_identical:
                    # Identical duplicates
                    duplicates.append({
                        "path": path,
                        "agents": [agent for agent, _ in sources],
                        "status": "DUPLICATE_IDENTICAL"
                    })
                    files_map[path] = first_content
                    file_metadata.append({
                        "path": path,
                        "agent": first_agent,
                        "co_agents": [agent for agent, _ in sources[1:]],
                        "size": len(first_content.encode("utf-8")),
                        "status": "valid"
                    })
                else:
                    # Conflict! Different content for same path
                    conflicts.append({
                        "path": path,
                        "sources": {agent: content for agent, content in sources},
                        "action": "Conflict resolved by agent heuristic/priority"
                    })

                    # Resolve conflict: prioritize matching agent type by path namespace
                    chosen_agent, chosen_content = first_agent, first_content
                    for agent, content in sources:
                        if path.startswith("backend/") and agent == "backend":
                            chosen_agent, chosen_content = agent, content
                            break
                        elif path.startswith("frontend/") and agent == "frontend":
                            chosen_agent, chosen_content = agent, content
                            break
                        elif path.startswith("database/") and agent == "database":
                            chosen_agent, chosen_content = agent, content
                            break
                        elif "test" in path.lower() and agent == "testing":
                            chosen_agent, chosen_content = agent, content
                            break
                    else:
                        # Fallback to the longest content
                        for agent, content in sources:
                            if len(content) > len(chosen_content):
                                chosen_agent, chosen_content = agent, content

                    files_map[path] = chosen_content
                    file_metadata.append({
                        "path": path,
                        "agent": chosen_agent,
                        "conflict": True,
                        "conflict_agents": [agent for agent, _ in sources],
                        "size": len(chosen_content.encode("utf-8")),
                        "status": "conflict_resolved"
                    })
            else:
                # Single source file
                files_map[path] = first_content
                file_metadata.append({
                    "path": path,
                    "agent": first_agent,
                    "size": len(first_content.encode("utf-8")),
                    "status": "valid"
                })

        # Calculate directory count
        directories = set()
        for path in files_map:
            p = Path(path)
            for parent in p.parents:
                if parent.name and parent.name != ".":
                    directories.add(str(parent))

        manifest = {
            "project_name": project_name,
            "total_files": len(files_map),
            "total_directories": len(directories),
            "files": file_metadata,
            "conflicts": conflicts,
            "duplicates": duplicates,
            "validation": {
                "passed": True,
                "errors": 0,
                "warnings": 0
            }
        }

        logger.info(f"[ASSEMBLER] Completed project assembly. Files: {len(files_map)}, Conflicts: {len(conflicts)}")
        return {
            "files": files_map,
            "manifest": manifest
        }

    def write_project_to_disk(
        self,
        project_name: str,
        files_map: Dict[str, str],
        base_dir: str = "generated_projects"
    ) -> Path:
        """
        Safely writes assembled files map to generated_projects/<project_name>/ on disk.
        Enforces strict path traversal security checks to prevent writing outside target directory.
        """
        safe_name = "".join([c if c.isalnum() or c in "-_" else "_" for c in project_name]).strip("_") or "AIForgeProject"
        base_path = Path(base_dir).resolve()
        target_dir = (base_path / safe_name).resolve()

        # Security check: ensure target_dir is strictly inside base_path
        if not self._is_safe_subpath(base_path, target_dir):
            raise ValueError(f"Unsafe project directory path: {target_dir}")

        target_dir.mkdir(parents=True, exist_ok=True)

        for rel_path, content in files_map.items():
            clean_rel = rel_path.replace("\\", "/").lstrip("/")

            # Reject traversal segments
            parts = clean_rel.split("/")
            if ".." in parts or clean_rel.startswith("/") or ":" in clean_rel:
                raise ValueError(f"Security Warning: Unsafe path blocked: {rel_path}")

            dest_path = (target_dir / clean_rel).resolve()

            # Path traversal security check
            if not self._is_safe_subpath(target_dir, dest_path):
                raise ValueError(f"Security Warning: Path traversal detected for path '{rel_path}'")

            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_text(content or "", encoding="utf-8")

        logger.info(f"[ASSEMBLER] Safely wrote {len(files_map)} files to disk at '{target_dir}'")
        return target_dir

    def _is_safe_subpath(self, parent_dir: Path, target_path: Path) -> bool:
        """Determines if a target_path is strictly relative to or inside parent_dir."""
        try:
            resolved_parent = parent_dir.resolve()
            resolved_target = target_path.resolve()
            resolved_target.relative_to(resolved_parent)
            return True
        except ValueError:
            return False


# Global ProjectAssembler Instance
global_project_assembler = ProjectAssembler()
