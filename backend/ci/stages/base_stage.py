"""
Base CI Stage Abstraction
=========================
"""

import time
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional

from backend.ci.models import CIStageResult, CIStageStatus
from backend.execution.models import ExecutionStatus, ProjectExecutionResult
from backend.execution.project_detector import DetectedProjectConfig
from backend.execution.execution_backend import ExecutionBackend

_logger = logging.getLogger("aiforge.ci.stage")


class CIStageBase(ABC):
    """
    Abstract Base Class for all CI pipeline stages.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def execute(
        self,
        sandbox_path: Path,
        project_cfg: DetectedProjectConfig,
        backend: ExecutionBackend,
        timeout: float,
        custom_env: Optional[Dict[str, str]] = None,
        files_manifest: Optional[Dict[str, str]] = None
    ) -> CIStageResult:
        """
        Executes the CI stage inside the sandbox and returns a structured CIStageResult.
        """
        pass
