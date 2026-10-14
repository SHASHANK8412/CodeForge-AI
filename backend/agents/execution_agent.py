"""
AIForge Autonomous Engineering Platform — ExecutionAgent
=========================================================
Runs generated project in isolated sandbox, detects project type & framework,
executes build, test, and startup processes, capturing structured metrics.
"""

import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from backend.agents.base_agent import BaseAgent
from backend.execution.project_detector import global_project_detector, DetectedProjectConfig
from backend.execution.sandbox_manager import global_sandbox_manager, ExecutionResult

_logger = logging.getLogger("aiforge.agents.execution_agent")


class ExecutionAgentReport(BaseModel):
    status: str = "success"  # "success", "failed", "timeout", "security_violation"
    exit_code: int = 0
    error_type: Optional[str] = None
    error_message: str = ""
    stdout: str = ""
    stderr: str = ""
    duration_ms: float = 0.0
    failed_command: str = ""
    project_config: Dict[str, Any] = Field(default_factory=dict)


class ExecutionAgent(BaseAgent):
    """
    Dedicated Execution Agent gating build, test, and runtime validation.
    """

    def __init__(self):
        super().__init__(
            system_prompt=(
                "You are the Execution Agent for AIForge. Your job is to execute "
                "generated project code in an isolated sandbox, run build and test commands, "
                "and capture structured execution metrics and error output."
            ),
            task_name="execution"
        )

    def execute_project(
        self,
        files_manifest: Dict[str, str],
        project_dir: Optional[str] = None,
        timeout: int = 30
    ) -> ExecutionAgentReport:
        _logger.info(f"[ExecutionAgent] Running sandbox execution for {len(files_manifest)} files...")

        # 1. Detect Project Type & Config
        config: DetectedProjectConfig = global_project_detector.detect(files_manifest)

        # 2. Choose primary command (build or test)
        command_to_run = config.build_command
        if not command_to_run or "echo" in command_to_run:
            command_to_run = config.test_command

        # 3. Run in Sandboxed Execution Layer
        exec_res: ExecutionResult = global_sandbox_manager.execute_command(
            command_str=command_to_run,
            cwd=project_dir,
            timeout=timeout
        )

        return ExecutionAgentReport(
            status=exec_res.status,
            exit_code=exec_res.exit_code,
            error_type=exec_res.error_type,
            error_message=exec_res.error_message,
            stdout=exec_res.stdout,
            stderr=exec_res.stderr,
            duration_ms=exec_res.duration_ms,
            failed_command=exec_res.failed_command,
            project_config=config.model_dump()
        )


global_execution_agent = ExecutionAgent()
