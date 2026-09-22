"""
AIForge Autonomous CI/CD Pipeline Engine
========================================
Coordinates full multi-stage CI execution:
Dependency -> Build -> Test -> Lint -> Security
Enforces Docker container isolation and executes closed-loop AI self-debugging
upon stage failures up to MAX_CI_REPAIR_ATTEMPTS.
"""

import sys
import time
import shutil
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable

from backend import config as app_config
from backend.ci.models import (
    CIConfig,
    CIStageResult,
    CIStageStatus,
    CIOverallStatus,
    CIPipelineResult,
)
from backend.ci.stages import (
    DependencyStage,
    BuildStage,
    TestStage,
    LintStage,
    SecurityStage,
)
from backend.ci.github_actions_generator import GitHubActionsGenerator, global_github_actions_generator
from backend.ci.history_store import CIHistoryStore, global_ci_history_store
from backend.execution.project_detector import ProjectDetector, DetectedProjectConfig
from backend.execution.execution_service import ExecutionService, global_execution_service
from backend.execution.error_classifier import ErrorClassifier
from backend.agents.debug_agent import DebugAgent, global_debug_agent

_logger = logging.getLogger("aiforge.ci.pipeline")


class CIPipelineEngine:
    """
    Autonomous CI/CD Pipeline Engine with closed-loop AI failure recovery.
    """

    def __init__(
        self,
        execution_service: Optional[ExecutionService] = None,
        debug_agent: Optional[DebugAgent] = None,
        github_generator: Optional[GitHubActionsGenerator] = None,
        history_store: Optional[CIHistoryStore] = None
    ):
        self.execution_service = execution_service or global_execution_service
        self.debug_agent = debug_agent or global_debug_agent
        self.detector = ProjectDetector()
        self.error_classifier = ErrorClassifier()
        self.github_generator = github_generator or global_github_actions_generator
        self.history_store = history_store or global_ci_history_store

        # Ordered pipeline stages
        self.stages = [
            DependencyStage(),
            BuildStage(),
            TestStage(),
            LintStage(),
            SecurityStage(),
        ]

    def _prepare_sandbox(self, files_manifest: Dict[str, str]) -> Tuple[tempfile.TemporaryDirectory, Path, Dict[str, str]]:
        """Creates a dedicated temporary workspace populated with project files."""
        temp_dir = tempfile.TemporaryDirectory(prefix="aiforge_ci_sandbox_")
        sandbox_path = Path(temp_dir.name).resolve()

        current_manifest = dict(files_manifest)
        for rel_path, content in current_manifest.items():
            clean_rel = rel_path.replace("\\", "/").lstrip("/")
            if ".." in clean_rel or clean_rel.startswith("/"):
                continue
            dest = (sandbox_path / clean_rel).resolve()
            if not str(dest).startswith(str(sandbox_path)):
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")

        # Ensure python subpackages have __init__.py
        for sub_name in ["backend", "tests", "src"]:
            sub_dir = sandbox_path / sub_name
            if sub_dir.exists() and not (sub_dir / "__init__.py").exists():
                (sub_dir / "__init__.py").write_text("", encoding="utf-8")
                current_manifest[f"{sub_name}/__init__.py"] = ""

        return temp_dir, sandbox_path, current_manifest

    def execute_pipeline(
        self,
        files_manifest: Dict[str, str],
        project_id: str = "default_project",
        commit_version: str = "main",
        config: Optional[CIConfig] = None,
        stage_callback: Optional[Callable[[CIStageResult], None]] = None
    ) -> CIPipelineResult:
        """
        Executes the full Autonomous CI/CD Pipeline:
        Dependencies -> Build -> Test -> Lint -> Security
        With automatic failure debugging and repair attempts.
        """
        cfg = config or CIConfig()
        overall_start_time = time.perf_counter()
        applied_repairs: List[Dict[str, Any]] = []
        modified_files_set = set()
        last_container_id = None

        # Resolve execution backend (Docker or Local)
        backend = self.execution_service.get_backend(
            backend_name="docker" if (cfg.docker_enabled or cfg.execution_backend == "docker") else "local"
        )
        backend_name = "docker" if cfg.docker_enabled or cfg.execution_backend == "docker" else "local"

        temp_dir, sandbox_path, current_manifest = self._prepare_sandbox(files_manifest)

        try:
            detected_cfg = self.detector.detect(current_manifest)
            project_type = f"{detected_cfg.language}:{detected_cfg.framework}"

            attempt = 0
            pipeline_passed = False
            stage_results_map: Dict[str, CIStageResult] = {}
            ordered_stage_results: List[CIStageResult] = []

            while attempt <= cfg.max_repair_attempts and not pipeline_passed:
                ordered_stage_results.clear()
                stage_results_map.clear()
                stage_failed = False
                failed_stage_result: Optional[CIStageResult] = None

                for stage in self.stages:
                    _logger.info(f"CI [Attempt {attempt}]: Executing stage '{stage.name}' for '{project_id}'")
                    res = stage.execute(
                        sandbox_path=sandbox_path,
                        project_cfg=detected_cfg,
                        backend=backend,
                        timeout=cfg.timeout_seconds,
                        custom_env=cfg.environment_variables,
                        files_manifest=current_manifest
                    )
                    ordered_stage_results.append(res)
                    stage_results_map[res.stage] = res

                    if stage_callback:
                        try:
                            stage_callback(res)
                        except Exception as cb_err:
                            _logger.debug(f"Callback error: {cb_err}")

                    if res.status == CIStageStatus.FAILED.value:
                        stage_failed = True
                        failed_stage_result = res
                        break
                    elif res.status == CIStageStatus.TIMEOUT.value:
                        stage_failed = True
                        failed_stage_result = res
                        break

                if not stage_failed:
                    pipeline_passed = True
                    break

                # Handle failure: If retries left, invoke DebugAgent
                if attempt < cfg.max_repair_attempts and failed_stage_result:
                    attempt += 1
                    _logger.info(f"CI Stage '{failed_stage_result.stage}' failed. Initiating repair attempt {attempt}/{cfg.max_repair_attempts}")

                    error_category = self.error_classifier.classify(
                        f"{failed_stage_result.stdout}\n{failed_stage_result.stderr}"
                    )

                    state_payload = {
                        "execution_results": {
                            "status": "FAIL",
                            "exit_code": failed_stage_result.exit_code,
                            "stdout": failed_stage_result.stdout,
                            "stderr": failed_stage_result.stderr,
                            "failed_command": failed_stage_result.command,
                            "error_type": error_category,
                            "failed_stage": failed_stage_result.stage
                        },
                        "files": current_manifest,
                        "project_path": str(sandbox_path)
                    }

                    debug_res = self.debug_agent.diagnose_and_repair(state_payload)
                    changes = debug_res.changes or {}
                    files_patched = []

                    for rel_path, updated_code in changes.items():
                        clean_rel = rel_path.replace("\\", "/").lstrip("/")
                        dest = (sandbox_path / clean_rel).resolve()
                        if not str(dest).startswith(str(sandbox_path)):
                            continue
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_text(updated_code, encoding="utf-8")
                        current_manifest[clean_rel] = updated_code
                        files_patched.append(clean_rel)
                        modified_files_set.add(clean_rel)

                    applied_repairs.append({
                        "attempt": attempt,
                        "failed_stage": failed_stage_result.stage,
                        "diagnosis": debug_res.diagnosis,
                        "root_cause": debug_res.root_cause,
                        "error_type": debug_res.error_type,
                        "modified_files": files_patched,
                        "confidence": debug_res.confidence
                    })

                    if not files_patched:
                        _logger.warning("DebugAgent did not provide file modifications. Halting repair loop.")
                        break
                else:
                    # Max repair attempts reached
                    break

            total_duration = round(time.perf_counter() - overall_start_time, 2)
            overall_status = CIOverallStatus.PASSED.value if pipeline_passed else CIOverallStatus.FAILED.value

            # Check if any stage timed out
            if any(st.status == CIStageStatus.TIMEOUT.value for st in ordered_stage_results):
                overall_status = CIOverallStatus.TIMEOUT.value

            # Generate GitHub Actions workflow
            workflow_yaml = ""
            if cfg.generate_github_workflow:
                workflow_yaml = self.github_generator.generate_workflow(
                    files_manifest=current_manifest,
                    project_name=project_id,
                    detected_cfg=detected_cfg
                )

            final_result = CIPipelineResult(
                project_id=project_id,
                project_type=project_type,
                commit_version=commit_version,
                status=overall_status,
                build=stage_results_map.get("build", CIStageResult(stage="build", status="skipped")).model_dump(),
                tests=stage_results_map.get("tests", CIStageResult(stage="tests", status="skipped")).model_dump(),
                lint=stage_results_map.get("lint", CIStageResult(stage="lint", status="skipped")).model_dump(),
                security=stage_results_map.get("security", CIStageResult(stage="security", status="skipped")).model_dump(),
                dependencies=stage_results_map.get("dependencies", CIStageResult(stage="dependencies", status="skipped")).model_dump(),
                repair_attempts=attempt,
                max_repair_attempts=cfg.max_repair_attempts,
                duration=total_duration,
                stages=ordered_stage_results,
                applied_repairs=applied_repairs,
                files_modified=sorted(list(modified_files_set)),
                workflow_yaml=workflow_yaml,
                backend_used=backend_name,
                container_id=last_container_id
            )

            # Persist in history store
            self.history_store.save_run(final_result)
            return final_result

        finally:
            backend.cleanup()
            try:
                temp_dir.cleanup()
            except Exception:
                pass


global_ci_pipeline_engine = CIPipelineEngine()
