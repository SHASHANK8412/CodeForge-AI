"""
AIForge Specification Manager Module
====================================
Manages project specification storage, versioning (v1.0 -> v1.1), diffing, and REQUIREMENTS.md generation.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.requirements.models import ProjectSpecification, ChangeImpact

_logger = logging.getLogger("aiforge.requirements.specification_manager")


class SpecificationManager:
    """
    Persists and version-controls ProjectSpecification instances.
    """

    def __init__(self):
        self._specs: Dict[str, ProjectSpecification] = {}

    def get_specification(self, project_id: str) -> Optional[ProjectSpecification]:
        return self._specs.get(project_id)

    def save_specification(self, project_id: str, spec: ProjectSpecification, project_path: Optional[Path] = None):
        self._specs[project_id] = spec
        if project_path and project_path.exists():
            self.write_requirements_md(project_path, spec)
        _logger.info(f"SpecificationManager: Saved spec v{spec.version} for '{project_id}'")

    def apply_change_impact(
        self,
        project_id: str,
        impact: ChangeImpact,
        project_path: Optional[Path] = None
    ) -> ProjectSpecification:
        spec = self._specs.get(project_id)
        if not spec:
            raise ValueError(f"Specification for project '{project_id}' not found.")

        v_parts = spec.version.split(".")
        new_v = f"{v_parts[0]}.{int(v_parts[1]) + 1}" if len(v_parts) == 2 else "1.1"
        spec.version = new_v

        for new_req in impact.new_requirements:
            if new_req.category == "SECURITY":
                spec.security_requirements.append(new_req)
            else:
                spec.functional_requirements.append(new_req)

        self.save_specification(project_id, spec, project_path)
        return spec

    def write_requirements_md(self, project_path: Path, spec: ProjectSpecification):
        md_lines = [
            f"# {spec.project_name} — Software Specification (v{spec.version})",
            f"**Project Type**: `{spec.project_type}` | **Coverage**: `{spec.coverage_score}%`\n",
            "## Functional Requirements",
        ]

        for fr in spec.functional_requirements:
            status = "✓" if fr.is_verified else ("[ ]" if not fr.is_implemented else "⚙")
            md_lines.append(f"- **{fr.id}**: {fr.title} — *{fr.description}* ({status})")

        md_lines.append("\n## Security Requirements")
        for sec in spec.security_requirements:
            md_lines.append(f"- **{sec.id}**: {sec.title} — *{sec.description}*")

        md_lines.append("\n## User Stories")
        for us in spec.user_stories:
            md_lines.append(f"- **{us.id}**: As a {us.as_a}, I want {us.i_want}, so that {us.so_that}.")

        md_lines.append("\n## Acceptance Criteria")
        for ac in spec.acceptance_criteria:
            md_lines.append(f"- **{ac.id}**: Given {ac.given}, When {ac.when}, Then {ac.then}.")

        md_lines.append("\n## Assumptions")
        for a in spec.assumptions:
            md_lines.append(f"- {a}")

        try:
            (project_path / "REQUIREMENTS.md").write_text("\n".join(md_lines), encoding="utf-8")
        except Exception as e:
            _logger.error(f"Failed to write REQUIREMENTS.md: {e}")


global_specification_manager = SpecificationManager()
