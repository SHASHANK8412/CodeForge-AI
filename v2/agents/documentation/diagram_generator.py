"""
AIForge V2 – Mermaid Diagram Generator
======================================
Generates Mermaid diagrams (Flowcharts, Sequence Diagrams, ER Diagrams).
"""

from typing import List
from v2.agents.documentation.models import MermaidDiagramSpec


class DiagramGenerator:

    def generate_default_diagrams(self) -> List[MermaidDiagramSpec]:
        return [
            MermaidDiagramSpec(
                title="AIForge V2 Autonomous Agent Pipeline Flowchart",
                diagram_type="Flowchart",
                mermaid_code="""graph TD
  User --> CEO
  CEO --> Manager
  Manager --> Planner
  Planner --> Architect
  Architect --> Frontend
  Architect --> Backend
  Architect --> Database
  Database --> Reviewer
  Reviewer --> Testing
  Testing --> Documentation
"""
            ),
            MermaidDiagramSpec(
                title="PostgreSQL Entity Relationship (ER) Diagram",
                diagram_type="ER",
                mermaid_code="""erDiagram
  users ||--o{ projects : "owns"
  projects ||--o{ tasks : "contains"
  projects ||--o{ agent_logs : "records"
"""
            )
        ]


global_diagram_generator = DiagramGenerator()
