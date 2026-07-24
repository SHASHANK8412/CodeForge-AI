"""
AIForge Day 96 & 97 Database Models & Schema
============================================
Data structures for Project Memory, Lessons Learned, Best Practices, and Reflection logs.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import time


@dataclass
class ProjectMemoryModel:
    id: str
    prompt: str
    architecture: str
    agents_used: List[str] = field(default_factory=lambda: ["Planner", "Architect", "Frontend", "Backend", "Reviewer", "Learning"])
    generated_files: List[str] = field(default_factory=list)
    bugs: List[str] = field(default_factory=list)
    fixes: List[str] = field(default_factory=list)
    tests: Dict[str, Any] = field(default_factory=lambda: {"passed": 36, "total": 38, "coverage_pct": 94.7})
    review_score: float = 95.6
    performance: Dict[str, Any] = field(default_factory=lambda: {"generation_time_sec": 48, "tokens": 3400})
    timestamp: float = field(default_factory=time.time)


@dataclass
class LessonLearnedModel:
    id: str
    category: str
    problem: str
    fix: str
    times_applied: int = 1
    timestamp: float = field(default_factory=time.time)


@dataclass
class ReflectionLogModel:
    id: str
    project_id: str
    what_went_well: List[str]
    what_failed: List[str]
    architecture_improvements: List[str]
    security_concerns: List[str]
    overall_score: float = 95.6
    timestamp: float = field(default_factory=time.time)
