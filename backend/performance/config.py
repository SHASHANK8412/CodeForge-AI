"""
AIForge Quality Recovery Day 14 — Performance & Reliability Configuration
==========================================================================
Centralized configuration flags, limits, timeouts, and tuning parameters.
"""

import os
from dataclasses import dataclass, field


@dataclass
class PerformanceConfig:
    """Centralized Performance & Reliability Configuration."""

    # Feature Flags
    AIFORGE_FAST_PATH_ENABLED: bool = field(default_factory=lambda: os.getenv("AIFORGE_FAST_PATH_ENABLED", "true").lower() == "true")
    AIFORGE_CACHE_ENABLED: bool = field(default_factory=lambda: os.getenv("AIFORGE_CACHE_ENABLED", "true").lower() == "true")
    AIFORGE_PARALLEL_EXECUTION_ENABLED: bool = field(default_factory=lambda: os.getenv("AIFORGE_PARALLEL_EXECUTION_ENABLED", "true").lower() == "true")
    AIFORGE_STREAMING_ENABLED: bool = field(default_factory=lambda: os.getenv("AIFORGE_STREAMING_ENABLED", "true").lower() == "true")
    AIFORGE_CIRCUIT_BREAKER_ENABLED: bool = field(default_factory=lambda: os.getenv("AIFORGE_CIRCUIT_BREAKER_ENABLED", "true").lower() == "true")
    AIFORGE_CHECKPOINTING_ENABLED: bool = field(default_factory=lambda: os.getenv("AIFORGE_CHECKPOINTING_ENABLED", "true").lower() == "true")
    AIFORGE_PERFORMANCE_TRACING_ENABLED: bool = field(default_factory=lambda: os.getenv("AIFORGE_PERFORMANCE_TRACING_ENABLED", "true").lower() == "true")
    AIFORGE_DEBUG_METRICS_ENABLED: bool = field(default_factory=lambda: os.getenv("AIFORGE_DEBUG_METRICS_ENABLED", "true").lower() == "true")

    # Centralized Model & Tool Call Budgets
    MAX_MODEL_CALLS_FAST: int = 1
    MAX_MODEL_CALLS_STANDARD: int = 3
    MAX_MODEL_CALLS_WORKFLOW: int = 10

    # Centralized Concurrency Limits
    MAX_CONCURRENT_LLM_CALLS: int = 4
    MAX_CONCURRENT_TOOL_CALLS: int = 4
    MAX_CONCURRENT_TESTS: int = 2
    MAX_CONCURRENT_WORKFLOWS_PER_SESSION: int = 2

    # Centralized Timeouts (seconds)
    REQUEST_TIMEOUT_SECONDS: float = 60.0
    WORKFLOW_TIMEOUT_SECONDS: float = 300.0
    LLM_CONNECT_TIMEOUT_SECONDS: float = 5.0
    LLM_READ_TIMEOUT_SECONDS: float = 30.0
    SANDBOX_TIMEOUT_SECONDS: float = 15.0
    TEST_EXECUTION_TIMEOUT_SECONDS: float = 20.0
    RAG_SEARCH_TIMEOUT_SECONDS: float = 10.0
    GIT_OPERATION_TIMEOUT_SECONDS: float = 15.0

    # Retry & Circuit Breaker Settings
    MAX_RETRIES: int = 3
    RETRY_INITIAL_DELAY_SECONDS: float = 0.5
    RETRY_MAX_DELAY_SECONDS: float = 5.0
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 3
    CIRCUIT_BREAKER_RECOVERY_SECONDS: float = 10.0

    # Cache Settings
    MAX_CACHE_ENTRIES: int = 1000
    CACHE_DEFAULT_TTL_SECONDS: float = 3600.0
    PROMPT_VERSION: str = "v14.0"
    MODEL_VERSION: str = "v1.0"


global_performance_config = PerformanceConfig()
