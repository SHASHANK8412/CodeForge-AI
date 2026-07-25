"""
AIForge V2 – Database Agent Data Models
=======================================
Data structures for Tables, Relationships, SQLAlchemy ORM Models, Alembic Migrations,
Indexes, Seed Data, Backup Strategies, and Monitoring Configurations.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TableDefinitionSpec(BaseModel):
    table_name: str
    description: str
    columns: List[Dict[str, Any]]
    primary_key: str = "id"
    foreign_keys: List[Dict[str, str]] = Field(default_factory=list)
    indexes: List[str] = Field(default_factory=list)


class RelationshipSpec(BaseModel):
    parent_table: str
    child_table: str
    rel_type: str  # 1:1, 1:N, M:N
    foreign_key_col: str


class IndexSpec(BaseModel):
    index_name: str
    table_name: str
    columns: List[str]
    is_unique: bool = False


class MigrationSpec(BaseModel):
    revision_id: str
    description: str
    up_script: str
    down_script: str


class SeedDataSpec(BaseModel):
    table_name: str
    records: List[Dict[str, Any]]


class BackupConfigSpec(BaseModel):
    backup_schedule: str = "Daily at 02:00 UTC"
    retention_days: int = 30
    backup_script: str
    restore_script: str


class MonitoringConfigSpec(BaseModel):
    slow_query_threshold_ms: float = 200.0
    max_connections: int = 100
    vacuum_schedule: str = "Weekly Sunday 03:00 UTC"


class DatabaseReport(BaseModel):
    project_id: str
    project_name: str
    folder_structure: List[str]
    ddl_schema_sql: str
    sqlalchemy_models_code: str
    tables: List[TableDefinitionSpec]
    relationships: List[RelationshipSpec]
    indexes: List[IndexSpec]
    migrations: List[MigrationSpec]
    seeds: List[SeedDataSpec]
    backup_config: BackupConfigSpec
    monitoring_config: MonitoringConfigSpec
    build_status: str = "success"
    confidence_score: float = 98.0
