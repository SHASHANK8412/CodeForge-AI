"""
AIForge Autonomous Code Execution & Validation Engine
=====================================================
Executes, tests, and validates generated projects inside controlled temporary
sandbox workspaces with closed-loop self-debugging, automated repair patching,
and structured validation reporting.
"""

import os
import sys
import time
import shutil
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable

from backend.execution.models import (
    ExecutionLimits,
    ExecutionResult,
    ExecutionStatus,
    PipelineStep,
    PipelineStepResult,
    ProjectExecutionResult,
    FinalValidationReport,
    AutonomousValidationConfig,
    TestResult,
    DebugResult,
)
from backend.execution.project_detector import ProjectDetector, DetectedProjectConfig
from backend.execution.error_classifier import ErrorClassifier
from backend.agents.debug_agent import DebugAgent, global_debug_agent
from backend.agents.testing_agent import TestingAgent

_logger = logging.getLogger("aiforge.execution.autonomous_engine")


class SandboxSecurityError(Exception):
    """Raised when an operation violates sandbox safety constraints."""
    pass


from backend.execution.execution_backend import (
    ExecutionBackend,
    LocalExecutionBackend,
    DockerExecutionBackend,
)
from backend.execution.execution_service import (
    ExecutionService,
    global_execution_service,
)

# Backward-compatible aliases
ExecutionSandboxBase = ExecutionBackend
SubprocessSandboxRunner = LocalExecutionBackend
DockerSandboxRunner = DockerExecutionBackend


class AutonomousExecutionEngine:
    """
    Orchestrates the Autonomous Code Execution & Validation Pipeline:
    1. Prepares controlled sandbox workspace.
    2. Detects project type and suitable commands (Python, Node.js, React/Vite).
    3. Installs dependencies inside sandbox workspace.
    4. Executes application tests/validation.
    5. Captures execution evidence (stdout, stderr, exit code, duration).
    6. Integrates with Testing Agent for result evaluation.
    7. On failure: invokes Debug Agent, applies synthesized code patches, and repeats up to retry limit.
    8. Produces comprehensive FinalValidationReport.
    """

    def __init__(
        self,
        config: Optional[AutonomousValidationConfig] = None,
        debug_agent: Optional[DebugAgent] = None,
        testing_agent: Optional[TestingAgent] = None,
        execution_service: Optional[ExecutionService] = None
    ):
        self.config = config or AutonomousValidationConfig()
        self.detector = ProjectDetector()
        self.error_classifier = ErrorClassifier()
        self.debug_agent = debug_agent or global_debug_agent
        self.testing_agent = testing_agent or TestingAgent()
        self.execution_service = execution_service or global_execution_service
        self.runner: ExecutionBackend = self.execution_service.get_backend(config=self.config)

    def detect_project_type(self, files_manifest: Dict[str, str]) -> DetectedProjectConfig:
        """Detects project framework, package manager, and commands from manifest."""
        return self.detector.detect(files_manifest)

    def resolve_dependency_command(self, project_cfg: DetectedProjectConfig, target_dir: Path) -> Optional[List[str]]:
        """Resolves the dependency installation command based on detected project config and files."""
        pm = project_cfg.package_manager.lower()
        if pm in ["npm", "yarn", "pnpm"] or (target_dir / "package.json").exists():
            npm_cmd = "npm.cmd" if sys.platform == "win32" and shutil.which("npm.cmd") else (shutil.which("npm") or "npm")
            return [npm_cmd, "install", "--no-audit", "--no-fund"]
        elif pm == "pip" or (target_dir / "requirements.txt").exists():
            return [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        return None

    def resolve_test_command(self, project_cfg: DetectedProjectConfig, target_dir: Path) -> List[str]:
        """Resolves the test or verification command for the project."""
        lang = project_cfg.language.lower()
        if lang == "python":
            py_files = list(target_dir.glob("**/*.py"))
            has_tests = any("test" in p.name.lower() for p in py_files)
            if has_tests:
                target_arg = "tests" if (target_dir / "tests").exists() else "."
                # Use current python executable's pytest module with scoped target and fast flags
                return [sys.executable, "-m", "pytest", target_arg, "--rootdir=.", "-p", "no:langsmith", "-p", "no:cacheprovider", "-q"]
            main_file = "main.py"
            if (target_dir / "backend" / "main.py").exists():
                main_file = "backend/main.py"
            elif (target_dir / "main.py").exists():
                main_file = "main.py"
            return [sys.executable, "-m", "py_compile", main_file]

        elif lang in ["javascript", "typescript"]:
            pkg_json = target_dir / "package.json"
            npm_cmd = "npm.cmd" if sys.platform == "win32" and shutil.which("npm.cmd") else (shutil.which("npm") or "npm")
            if pkg_json.exists():
                try:
                    import json
                    data = json.loads(pkg_json.read_text(encoding="utf-8"))
                    scripts = data.get("scripts", {})
                    if "test" in scripts and "no test specified" not in scripts["test"]:
                        return [npm_cmd, "test"]
                    if "build" in scripts:
                        return [npm_cmd, "run", "build"]
                except Exception:
                    pass
            node_cmd = shutil.which("node") or "node"
            entry = target_dir / "index.js"
            if entry.exists():
                return [node_cmd, "index.js"]
            return [node_cmd, "-v"]

        return [sys.executable, "--version"]

    def _prepare_sandbox(
        self,
        files_manifest: Dict[str, str],
        source_dir: Optional[str] = None
    ) -> Tuple[tempfile.TemporaryDirectory, Path, Dict[str, str]]:
        """
        Creates a dedicated temporary sandbox workspace and populates it with project files.
        Guarantees path isolation and prevents directory traversal attacks.
        """
        temp_dir = tempfile.TemporaryDirectory(prefix="aiforge_exec_sandbox_")
        sandbox_path = Path(temp_dir.name).resolve()

        # Copy existing disk files if source directory is provided
        if source_dir and Path(source_dir).exists():
            src_path = Path(source_dir).resolve()
            for item in src_path.rglob("*"):
                if item.is_file() and ".git" not in item.parts and "__pycache__" not in item.parts and "node_modules" not in item.parts:
                    rel_path = item.relative_to(src_path)
                    dest = sandbox_path / rel_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        shutil.copy2(item, dest)
                    except Exception:
                        pass

        # Write or overwrite files from manifest
        current_manifest = dict(files_manifest)
        for rel_path, content in current_manifest.items():
            clean_rel = rel_path.replace("\\", "/").lstrip("/")
            if ".." in clean_rel or clean_rel.startswith("/"):
                _logger.warning(f"Path traversal detected and rejected in sandbox creation: {rel_path}")
                continue
            dest = (sandbox_path / clean_rel).resolve()
            if not str(dest).startswith(str(sandbox_path)):
                _logger.warning(f"Path traversal escaping sandbox rejected: {rel_path}")
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")

        # Ensure python subpackages have __init__.py
        for sub_name in ["backend", "tests"]:
            sub_dir = sandbox_path / sub_name
            if sub_dir.exists() and not (sub_dir / "__init__.py").exists():
                (sub_dir / "__init__.py").write_text("", encoding="utf-8")
                current_manifest[f"{sub_name}/__init__.py"] = ""

        return temp_dir, sandbox_path, current_manifest

    def execute_and_validate(
        self,
        files_manifest: Dict[str, str],
        project_name: str = "AIForgeProject",
        source_dir: Optional[str] = None,
        config: Optional[AutonomousValidationConfig] = None,
        step_callback: Optional[Callable[[PipelineStepResult], None]] = None
    ) -> FinalValidationReport:
        """
        Executes the full closed-loop autonomous validation pipeline:
        Preparing -> Installing dependencies -> Running tests -> On failure: Debug & Patch -> Retest -> Final Report.
        """
        cfg = config or self.config
        overall_start_time = time.perf_counter()
        steps_log: List[PipelineStepResult] = []
        applied_fixes: List[Dict[str, Any]] = []
        modified_files_set = set()
        last_container_id = None

        active_backend = self.execution_service.get_backend(config=cfg)
        is_docker = isinstance(active_backend, DockerExecutionBackend)
        backend_name = "docker" if is_docker else "local"

        def record_step(step: PipelineStep, status: str, cmd: str = "", stdout: str = "", stderr: str = "", code: int = 0, duration: float = 0.0, err_msg: str = "") -> PipelineStepResult:
            res = PipelineStepResult(
                step=step,
                status=status,
                command=cmd,
                stdout=stdout,
                stderr=stderr,
                exit_code=code,
                duration_ms=duration,
                error_message=err_msg
            )
            steps_log.append(res)
            if step_callback:
                try:
                    step_callback(res)
                except Exception as cb_err:
                    _logger.warning(f"Step callback error: {cb_err}")
            return res

        # If Docker backend is selected, log Docker container initialization step
        if is_docker:
            image_name = active_backend.select_docker_image()
            record_step(
                PipelineStep.DOCKER_STARTING,
                "SUCCESS",
                stdout=f"🐳 Starting Docker Sandbox (Image: {image_name}, Memory: {active_backend.memory_limit}, CPU: {active_backend.cpu_limit}, Network: {active_backend.network_mode})"
            )

        # 1. Preparing project in controlled temporary workspace
        prep_start = time.perf_counter()
        record_step(PipelineStep.PREPARING, "IN_PROGRESS")
        try:
            temp_dir, sandbox_path, current_manifest = self._prepare_sandbox(files_manifest, source_dir)
        except Exception as e:
            prep_dur = round((time.perf_counter() - prep_start) * 1000.0, 2)
            record_step(PipelineStep.PREPARING, "FAILED", duration=prep_dur, err_msg=str(e))
            return FinalValidationReport(
                project_name=project_name,
                project_type="unknown",
                overall_status="FAILED",
                total_duration_ms=prep_dur,
                attempts_count=0,
                max_attempts=cfg.max_repair_attempts,
                steps=steps_log,
                is_production_ready=False,
                backend_used=backend_name
            )

        prep_dur = round((time.perf_counter() - prep_start) * 1000.0, 2)
        record_step(PipelineStep.PREPARING, "SUCCESS", duration=prep_dur)

        # Detect project type
        proj_config = self.detect_project_type(current_manifest)
        project_type = f"{proj_config.language}:{proj_config.framework}"

        try:
            # 2. Dependency Installation
            if cfg.install_dependencies:
                dep_cmd = self.resolve_dependency_command(proj_config, sandbox_path)
                if dep_cmd:
                    record_step(PipelineStep.INSTALLING_DEPENDENCIES, "IN_PROGRESS", cmd=" ".join(dep_cmd))
                    dep_exec = active_backend.execute_command(
                        dep_cmd,
                        str(sandbox_path),
                        timeout_seconds=cfg.timeout_seconds * 2,  # Give dependencies slightly more time
                        max_output_bytes=cfg.max_output_bytes,
                        custom_env=cfg.environment_variables,
                        project_type=project_type
                    )
                    if dep_exec.container_id:
                        last_container_id = dep_exec.container_id
                    dep_status = "SUCCESS" if dep_exec.exit_code == 0 else "FAILED"
                    record_step(
                        PipelineStep.INSTALLING_DEPENDENCIES,
                        dep_status,
                        cmd=" ".join(dep_cmd),
                        stdout=dep_exec.stdout,
                        stderr=dep_exec.stderr,
                        code=dep_exec.exit_code,
                        duration=dep_exec.duration_ms,
                        err_msg="Dependency installation failed" if dep_exec.exit_code != 0 else ""
                    )
                    if dep_exec.exit_code != 0:
                        _logger.warning(f"Dependency installation failed: {dep_exec.stderr}")

            # 3. Validation & Self-Healing Loop
            attempt = 0
            tests_passed = False
            last_test_summary = None

            while attempt < cfg.max_repair_attempts and not tests_passed:
                attempt += 1
                is_retest = attempt > 1

                step_name = PipelineStep.RETESTING if is_retest else PipelineStep.RUNNING_TESTS
                test_cmd = self.resolve_test_command(proj_config, sandbox_path)
                record_step(step_name, "IN_PROGRESS", cmd=" ".join(test_cmd))

                # Execute test command
                test_exec = active_backend.execute_command(
                    test_cmd,
                    str(sandbox_path),
                    timeout_seconds=cfg.timeout_seconds,
                    max_output_bytes=cfg.max_output_bytes,
                    custom_env=cfg.environment_variables,
                    project_type=project_type
                )
                if test_exec.container_id:
                    last_container_id = test_exec.container_id

                # Evaluate execution results with Testing Agent / parser
                eval_dict = test_exec.model_dump()
                test_eval: TestResult = self.testing_agent.evaluate_execution_results(eval_dict)
                last_test_summary = test_eval.model_dump()

                # Execution passed if exit code is 0 and test result indicates success
                if test_exec.exit_code == 0 and test_eval.success:
                    tests_passed = True
                    record_step(
                        PipelineStep.TESTS_PASSED,
                        "SUCCESS",
                        cmd=" ".join(test_cmd),
                        stdout=test_exec.stdout,
                        stderr=test_exec.stderr,
                        code=test_exec.exit_code,
                        duration=test_exec.duration_ms
                    )
                    break

                # Tests or execution failed
                error_category = self.error_classifier.classify(f"{test_exec.stdout}\n{test_exec.stderr}")
                record_step(
                    PipelineStep.TESTS_FAILED,
                    "FAILED",
                    cmd=" ".join(test_cmd),
                    stdout=test_exec.stdout,
                    stderr=test_exec.stderr,
                    code=test_exec.exit_code,
                    duration=test_exec.duration_ms,
                    err_msg=f"Test failure ({error_category})"
                )

                if attempt >= cfg.max_repair_attempts:
                    _logger.info(f"Max repair attempts ({cfg.max_repair_attempts}) reached.")
                    break

                # 4. Invoke Debug Agent to analyze failures
                record_step(PipelineStep.DEBUGGING, "IN_PROGRESS")
                debug_start = time.perf_counter()

                state_payload = {
                    "execution_results": {
                        "status": "FAIL",
                        "exit_code": test_exec.exit_code,
                        "stdout": test_exec.stdout,
                        "stderr": test_exec.stderr,
                        "failed_command": " ".join(test_cmd),
                        "error_type": error_category
                    },
                    "test_results": last_test_summary,
                    "files": current_manifest,
                    "project_path": str(sandbox_path)
                }

                debug_result: DebugResult = self.debug_agent.diagnose_and_repair(state_payload)
                debug_dur = round((time.perf_counter() - debug_start) * 1000.0, 2)

                record_step(
                    PipelineStep.DEBUGGING,
                    "SUCCESS",
                    stdout=debug_result.explanation,
                    duration=debug_dur,
                    err_msg=debug_result.root_cause
                )

                # 5. Apply Fix to generated project in sandbox
                record_step(PipelineStep.APPLYING_FIX, "IN_PROGRESS")
                patch_start = time.perf_counter()

                changes = debug_result.changes or {}
                files_patched = []

                for rel_path, updated_content in changes.items():
                    clean_rel = rel_path.replace("\\", "/").lstrip("/")
                    if ".." in clean_rel or clean_rel.startswith("/"):
                        continue
                    dest = (sandbox_path / clean_rel).resolve()
                    if not str(dest).startswith(str(sandbox_path)):
                        continue
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(updated_content, encoding="utf-8")
                    current_manifest[clean_rel] = updated_content
                    files_patched.append(clean_rel)
                    modified_files_set.add(clean_rel)

                applied_fixes.append({
                    "attempt": attempt,
                    "diagnosis": debug_result.diagnosis,
                    "root_cause": debug_result.root_cause,
                    "error_type": debug_result.error_type,
                    "modified_files": files_patched,
                    "confidence": debug_result.confidence
                })

                patch_dur = round((time.perf_counter() - patch_start) * 1000.0, 2)
                record_step(
                    PipelineStep.APPLYING_FIX,
                    "SUCCESS" if files_patched else "NO_CHANGES",
                    stdout=f"Patched {len(files_patched)} file(s): {', '.join(files_patched)}",
                    duration=patch_dur
                )

            # 6. Final Result compilation
            total_duration = round((time.perf_counter() - overall_start_time) * 1000.0, 2)
            overall_status = "VERIFIED" if tests_passed else "FAILED_MAX_RETRIES"

            final_step_status = "SUCCESS" if tests_passed else "FAILED"
            record_step(
                PipelineStep.FINAL_RESULT,
                final_step_status,
                stdout=f"Pipeline finished with status: {overall_status} (Attempts: {attempt}/{cfg.max_repair_attempts})",
                duration=total_duration
            )

            report = FinalValidationReport(
                project_name=project_name,
                project_type=project_type,
                overall_status=overall_status,
                total_duration_ms=total_duration,
                attempts_count=attempt,
                max_attempts=cfg.max_repair_attempts,
                steps=steps_log,
                test_summary=last_test_summary,
                applied_fixes=applied_fixes,
                files_modified=sorted(list(modified_files_set)),
                is_production_ready=tests_passed,
                backend_used=backend_name,
                container_id=last_container_id
            )
            return report

        finally:
            try:
                active_backend.cleanup()
            except Exception:
                pass
            try:
                temp_dir.cleanup()
            except Exception:
                pass


global_autonomous_execution_engine = AutonomousExecutionEngine()
