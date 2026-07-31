"""
AIForge SRS Markdown Exporter (Day 50)
=====================================
Formats generated Software Requirement Specification (SRS) documents into structured Markdown/PDF exports.
"""

import time
import logging
from typing import Dict, Any

_logger = logging.getLogger("aiforge.product_manager.srs_exporter")


class SRSExporter:
    """
    Exports full SRS document payloads into clean Markdown format.
    """

    def export_to_markdown(self, srs_data: Dict[str, Any]) -> str:
        """
        Formats SRS dictionary into structured Markdown document.
        """
        md = f"# Software Requirement Specification (SRS): {srs_data.get('project_title', 'AIForge App')}\n\n"
        md += f"**Generated At:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        md += f"**Target Scale:** {srs_data.get('target_scale', 'Production Enterprise')}\n\n"

        md += "## 1. Functional Requirements\n"
        for req in srs_data.get("functional_requirements", []):
            md += f"- **[{req.get('id')}]** {req.get('description')}\n"

        md += "\n## 2. User Stories & Acceptance Criteria\n"
        for story in srs_data.get("user_stories", []):
            md += f"### Story: {story.get('as_a')} I want {story.get('i_want')} so that {story.get('so_that')}\n"
            md += f"**Acceptance Criteria:** {story.get('acceptance_criteria')}\n\n"

        md += "## 3. Sprint Roadmap & Milestones\n"
        for sprint in srs_data.get("sprint_plan", []):
            md += f"- **{sprint.get('sprint')}**: {sprint.get('goal')}\n"

        return md


global_srs_exporter = SRSExporter()
