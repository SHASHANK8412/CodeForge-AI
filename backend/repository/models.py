"""
AIForge Repository Intelligence Models
=======================================
Typed schemas for Repository Metadata, File Records, Symbol Records, Dependency Graphs,
Repository Maps, Impact Analysis, Change Plans, File Patches, and ChangeSets.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RepositoryInfo(BaseModel):
    """
    Typed summary of an indexed software repository.
    """
    repository_id: str = Field(description="Unique identifier for repository")
    root_path: str = Field(description="Sandboxed absolute root directory path")
    name: str = Field(description="Repository or directory name")
    languages: List[str] = Field(default_factory=list, description="Detected programming languages")
    frameworks: List[str] = Field(default_factory=list, description="Detected frameworks (FastAPI, React, Spring, etc.)")
    package_managers: List[str] = Field(default_factory=list, description="Detected package managers (pip, npm, maven, etc.)")
    test_frameworks: List[str] = Field(default_factory=list, description="Detected test frameworks (pytest, vitest, jest, etc.)")
    file_count: int = Field(default=0, description="Total file count")
    source_file_count: int = Field(default=0, description="Total source code file count")
    estimated_lines: int = Field(default=0, description="Estimated total source lines")


class SymbolRecord(BaseModel):
    """
    Structured code symbol (function, class, method, route, model).
    """
    name: str = Field(description="Symbol identifier name")
    kind: str = Field(description="Kind: 'function', 'class', 'method', 'route', 'model', 'interface', 'variable'")
    file: str = Field(description="Repository-relative file path")
    line_start: int = Field(default=1, description="Starting line number")
    line_end: int = Field(default=1, description="Ending line number")
    signature: str = Field(default="", description="Function or method signature")
    parent: str = Field(default="", description="Enclosing class or parent symbol name")


class FileRecord(BaseModel):
    """
    Metadata and index record for a repository file.
    """
    path: str = Field(description="Repository-relative file path")
    language: str = Field(default="python", description="File language identifier")
    size_bytes: int = Field(default=0, description="File size in bytes")
    purpose: str = Field(default="SOURCE", description="Purpose: 'SOURCE', 'TEST', 'CONFIG', 'DOCUMENTATION', 'ASSET', 'BUILD', 'UNKNOWN'")
    symbols: List[SymbolRecord] = Field(default_factory=list, description="Extracted code symbols")
    imports: List[str] = Field(default_factory=list, description="Imported modules or files")
    hash: str = Field(default="", description="SHA-256 hash of file content")
    is_binary: bool = Field(default=False, description="True if file is binary or asset")


class RepositoryMap(BaseModel):
    """
    Compact structural tree representation of a repository.
    """
    tree_text: str = Field(description="Concise directory structure tree")
    important_files: Dict[str, str] = Field(default_factory=dict, description="Map of path -> role label (ENTRY_POINT, ROUTE, MODEL, SERVICE, etc.)")


class RepositoryTask(BaseModel):
    """
    Analyzed task intent and target scope.
    """
    task_type: str = Field(default="MODIFY", description="Task type: 'READ_ONLY', 'ANALYZE', 'MODIFY', 'FEATURE', 'BUG_FIX', 'REFACTOR'")
    target_features: List[str] = Field(default_factory=list, description="Extracted target features (e.g. auth, user, payment)")
    target_symbols: List[str] = Field(default_factory=list, description="Target symbol names")
    keywords: List[str] = Field(default_factory=list, description="Key search terms")
    likely_layers: List[str] = Field(default_factory=list, description="Impacted architecture layers (route, service, model, test)")


class ImpactAnalysis(BaseModel):
    """
    Impact analysis result detailing primary and dependent target files.
    """
    primary_files: List[str] = Field(default_factory=list, description="Directly impacted target files")
    dependent_files: List[str] = Field(default_factory=list, description="Indirectly impacted files via import dependencies")
    candidate_tests: List[str] = Field(default_factory=list, description="Selected test files to run")
    risk_level: str = Field(default="MEDIUM", description="Risk level: 'LOW', 'MEDIUM', 'HIGH'")
    reason_labels: List[str] = Field(default_factory=list, description="Categorical justification labels")


class ChangePlan(BaseModel):
    """
    Structured plan for repository modifications.
    """
    goal: str = Field(description="Summary goal of the repository change")
    files_to_modify: List[str] = Field(default_factory=list, description="Target files to edit")
    files_to_create: List[str] = Field(default_factory=list, description="New files to create")
    tests_to_run: List[str] = Field(default_factory=list, description="Test files selected for verification")
    steps: List[str] = Field(default_factory=list, description="Ordered execution steps")
    risk: str = Field(default="MEDIUM", description="Assessed risk level")
    reasons: Dict[str, str] = Field(default_factory=dict, description="Map of file path -> justification reason")


class FilePatch(BaseModel):
    """
    Individual atomic file patch.
    """
    path: str = Field(description="Repository-relative target file path")
    operation: str = Field(default="MODIFY", description="Operation: 'MODIFY', 'CREATE', 'DELETE'")
    original_hash: str = Field(default="", description="Original SHA-256 hash before modification")
    updated_content: str = Field(description="New full content or patch")
    reason: str = Field(default="", description="Justification for file edit")


class ChangeSet(BaseModel):
    """
    Canonical result returned after repository modification.
    """
    files_created: List[str] = Field(default_factory=list, description="List of created files")
    files_modified: List[str] = Field(default_factory=list, description="List of modified files")
    files_deleted: List[str] = Field(default_factory=list, description="List of deleted files")
    tests_run: List[str] = Field(default_factory=list, description="List of executed test files")
    verification: str = Field(default="VERIFIED", description="VerificationStatus string")
    summary: str = Field(default="", description="Concise human-readable summary")
