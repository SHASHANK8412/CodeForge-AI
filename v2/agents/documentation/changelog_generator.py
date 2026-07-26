"""
AIForge V2 – Changelog & Release Notes Generator
================================================
Generates CHANGELOG.md and RELEASE_NOTES.md tracking versions, features, bug fixes, and breaking changes.
"""

from v2.agents.documentation.models import ReleaseNotesSpec


class ChangelogGenerator:

    def generate_release_notes(self) -> ReleaseNotesSpec:
        return ReleaseNotesSpec(
            version="2.0.0",
            summary="Autonomous AI Software Engineering Organization Release V2",
            features=[
                "CEO Agent (Project complexity evaluation & effort estimation)",
                "Project Manager Agent (Sprint milestone decomposition)",
                "Planner Agent (Product requirements blueprint)",
                "Architect Agent (Technical system topology & ER design)",
                "Frontend Agent (React + TSX + Tailwind application engine)",
                "Backend Agent (FastAPI REST routers, Services, Repositories, JWT Auth)",
                "Database Agent (PostgreSQL DDL, SQLAlchemy ORM, Alembic migrations)",
                "Reviewer Agent (Multi-dimensional code review & security audit)",
                "Testing Agent (Automated Pytest, Playwright E2E, Locust load benchmarks)",
                "Documentation Agent (Markdown guides, Mermaid diagrams, API references)"
            ],
            bug_fixes=[],
            breaking_changes=[]
        )


global_changelog_generator = ChangelogGenerator()
