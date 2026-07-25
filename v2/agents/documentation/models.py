"""
AIForge V2 – Documentation Agent Data Models
============================================
Data structures for Documentation Files, Mermaid Diagrams, Release Notes, and Validation Summaries.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class DocumentationFileSpec(BaseModel):
    file_name: str
    file_type: str  # README, Architecture, API, DB, Developer, Deployment, UserManual, Changelog
    path: str
    content_markdown: str


class MermaidDiagramSpec(BaseModel):
    title: str
    diagram_type: str  # Flowchart, Sequence, ER, Class, Component
    mermaid_code: str


class ReleaseNotesSpec(BaseModel):
    version: str = "2.0.0"
    summary: str
    features: List[str] = Field(default_factory=list)
    bug_fixes: List[str] = Field(default_factory=list)
    breaking_changes: List[str] = Field(default_factory=list)


class DocumentationReport(BaseModel):
    project_id: str
    project_name: str
    files: List[DocumentationFileSpec]
    diagrams: List[MermaidDiagramSpec]
    release_notes: ReleaseNotesSpec
    readme_markdown: str
    developer_docs_markdown: str
    deployment_docs_markdown: str
    user_manual_markdown: str
    build_status: str = "success"
    validation_score: float = 98.0
    confidence_score: float = 98.5
