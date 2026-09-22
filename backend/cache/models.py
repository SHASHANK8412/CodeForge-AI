"""
AIForge Day 28 — Job & Cache Pydantic Models
============================================
Data models for Background Jobs, Job Statuses, and Cache Metrics.
"""

from enum import Enum
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class JobType(str, Enum):
    PROJECT_GENERATION = "PROJECT_GENERATION"
    PERFORMANCE_ANALYSIS = "PERFORMANCE_ANALYSIS"
    BROWSER_TESTING = "BROWSER_TESTING"
    DEPLOYMENT = "DEPLOYMENT"
    RAG_INGESTION = "RAG_INGESTION"


class Job(BaseModel):
    id: str
    project_id: str = "aiforge-demo"
    type: JobType = JobType.PROJECT_GENERATION
    status: JobStatus = JobStatus.QUEUED
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    progress_step: str = "Queued"


class CachePerformanceMetric(BaseModel):
    cache_hits: int = 0
    cache_misses: int = 0
    before_latency_ms: float = 420.0
    after_latency_ms: float = 180.0
    hit_rate_pct: float = 0.0
    time_saved_ms: float = 0.0
