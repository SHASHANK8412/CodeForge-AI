import os
import sys
import subprocess
import logging
from pathlib import Path

from backend.review.test_parser import TestParser
from backend.review.debug import DebugAgent
from backend.review.patch_generator import PatchGenerator
from backend.review.patch_applier import PatchApplier
from backend.review.architecture_checker import ArchitectureChecker
from backend.review.security_checker import SecurityChecker
from backend.review.performance_checker import PerformanceChecker
from backend.review.quality_score import QualityScoreCalculator
from backend.review.report_generator import ReportGenerator
from backend.config import (
    MAX_RETRY,
    ENABLE_SELF_HEAL,
    ENABLE_SECURITY_SCAN,
    ENABLE_PERFORMANCE_SCAN,
)

_logger = logging.getLogger("aiforge.performance")


class SelfHealOrchestrator:
    """
    Main orchestration engine for automated code review, security checking,
    performance scans, test execution, error debugging, and self-healing patches.
    """

    def __init__(self) -> None:
        self.test_parser = TestParser()
        self.debug_agent = DebugAgent()
        self.patch_generator = PatchGenerator()
        self.patch_applier = PatchApplier()
        self.architecture_checker = ArchitectureChecker()
        self.security_checker = SecurityChecker()
        self.performance_checker = PerformanceChecker()
        self.quality_score_calculator = QualityScoreCalculator()
        self.report_generator = ReportGenerator()

    def run_tests(self, project_path: Path) -> tuple[int, str]:
        """
        Executes pytest in the generated project directory and captures the console output.
        """
        _logger.info(f"Running pytest tests on project: {project_path}")
        
        # Cross-platform execution using the running sys.executable (python)
        cmd = [sys.executable, "-m", "pytest", "tests/", "-v"]
        
        env = os.environ.copy()
        # Ensure project root is in PYTHONPATH so pytest can resolve imports
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = str(project_path) + os.pathsep + env["PYTHONPATH"]
        else:
            env["PYTHONPATH"] = str(project_path)

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(project_path),
                env=env,
                timeout=60
            )
            # Combine stdout and stderr
            output = res.stdout + "\n" + res.stderr
            return res.returncode, output
        except subprocess.TimeoutExpired as exc:
            _logger.warning("pytest run timed out after 60s")
            return -1, f"TimeoutExpired: pytest execution timed out.\n{exc.stdout or ''}"
        except Exception as exc:
            _logger.error(f"Failed to run pytest: {exc}")
            return -1, str(exc)

    async def execute_self_heal_pipeline(
        self,
        project_name: str,
        project_path: Path
    ) -> tuple[list[dict], dict, dict, str]:
        """
        Runs reviews and executes the test-debug-patch-retest loop,
        saving the quality score reports when finished.
        """
        _logger.info("INFO Review started")
        
        # 1. Statically analyze with Checkers
        findings = []
        findings.extend(self.architecture_checker.check_project(project_path))

        if ENABLE_SECURITY_SCAN:
            findings.extend(self.security_checker.check_project(project_path))

        if ENABLE_PERFORMANCE_SCAN:
            findings.extend(self.performance_checker.check_project(project_path))

        # 2. Start Self-Healing Retries Loop
        attempts = 0
        test_results = {"passed": 0, "failed": 0, "errors": 0, "failures_list": []}
        
        while attempts < MAX_RETRY:
            _logger.info(f"Running self-healing attempt {attempts + 1} of {MAX_RETRY}...")
            
            return_code, test_output = self.run_tests(project_path)
            
            # Exit code 0 means all passed, exit code 5 means no tests found (not an error)
            if return_code in [0, 5]:
                _logger.info("INFO Tests passed")
                test_results = self.test_parser.parse_pytest_output(test_output)
                break
            
            # Failures detected! Parse them.
            _logger.info("INFO Parsing test failures")
            test_results = self.test_parser.parse_pytest_output(test_output)
            
            if not ENABLE_SELF_HEAL:
                _logger.info("Self-heal disabled via configuration. Exiting loop.")
                break

            # Collect failing files
            failures = test_results.get("failures_list", [])
            if not failures:
                _logger.warning("Pytest failed but parser could not extract structured failures list.")
                break

            failing_files = list(set(f["file"] for f in failures))

            # Debug issues using LLM
            traceback_summary = "\n\n".join([
                f"Test: {f['test']}\nFile: {f['file']}\nTraceback:\n{f['traceback']}"
                for f in failures
            ])

            debug_info = await self.debug_agent.debug_failures(
                traceback=traceback_summary,
                pytest_output=test_output,
                failing_files=failing_files
            )

            # Generate patches for targeted file
            proposed_fix = debug_info.get("proposed_fix", "")
            
            # If proposed fix mentions a file, try that first. Otherwise try the first failing file.
            target_rel_file = failing_files[0]
            # Search if file path is in proposed fix
            for file in failing_files:
                if file in proposed_fix:
                    target_rel_file = file
                    break
            
            # For patch generation, we need the exact file path relative to project
            target_full_path = project_path / target_rel_file
            if not target_full_path.exists():
                # Fallback to backend/main.py if exists
                if (project_path / "backend/main.py").exists():
                    target_rel_file = "backend/main.py"
                    target_full_path = project_path / target_rel_file

            if target_full_path.exists():
                with open(target_full_path, "r", encoding="utf-8") as f:
                    file_content = f.read()

                patch = await self.patch_generator.generate_patch(
                    file_path=target_rel_file,
                    file_content=file_content,
                    proposed_fix=proposed_fix
                )

                if patch:
                    _logger.info("INFO Patch generated")
                    # Validate and Apply patch
                    success = self.patch_applier.apply_patch(project_path, patch)
                    if success:
                        _logger.info("INFO Patch validated")
                    else:
                        _logger.error("INFO Patch rejected")
                else:
                    _logger.error("Failed to generate code patch.")
            else:
                _logger.warning(f"Could not locate target file on disk for patching: {target_rel_file}")

            attempts += 1
            # Sleep brief moment between retries
            import asyncio
            await asyncio.sleep(0.5)

        # 3. Final Scoring and Report Compilation
        scores = self.quality_score_calculator.calculate_scores(findings, test_results)
        
        report_content = self.report_generator.generate_report_content(
            project_name=project_name,
            findings=findings,
            test_results=test_results,
            scores=scores
        )
        
        self.report_generator.write_report(project_path, report_content)
        _logger.info("INFO Validation completed")
        _logger.info("INFO ZIP exported successfully")

        return findings, test_results, scores, report_content
