"""
AIForge Benchmark Lab — Controlled Execution Engine
===================================================
Executes benchmark tasks across configurations in isolated workspaces with strict
resource limits, concurrency control, out-of-band validation, and cancellation.
"""

import os
import sys
import time
import shutil
import asyncio
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable, Awaitable

from backend.benchmark_lab.models import (
    BenchmarkTask,
    BenchmarkConfig,
    BenchmarkRun,
    TaskRunResult,
    WorkflowType,
)
from backend.benchmark_lab.tasks.library import get_task_by_id, ALL_BENCHMARK_TASKS
from backend.benchmark_lab.config_manager import global_config_manager
from backend.benchmark_lab.evaluator import global_objective_evaluator
from backend.execution.code_extractor import global_code_extractor

_logger = logging.getLogger("aiforge.benchmark_lab.engine")

# Directory for persisting benchmark run artifacts
RUNS_BASE_DIR = Path(__file__).resolve().parent.parent.parent / "benchmarks" / "runs"
NOT_RUN_EXIT_CODE = -2          # validation did not run (no sandbox, or no validator for the language)


class BenchmarkExecutionEngine:
    """
    Controlled execution service for multi-model benchmark evaluation.
    """

    def __init__(self, concurrency_limit: int = 1) -> None:
        self.semaphore = asyncio.Semaphore(concurrency_limit)
        self.cancelled_runs: set[str] = set()
        self._llm_completer: Optional[Callable[[str, str, Dict[str, Any]], Awaitable[str]]] = None
        RUNS_BASE_DIR.mkdir(parents=True, exist_ok=True)

    def set_llm_completer_override(self, fn: Optional[Callable[[str, str, Dict[str, Any]], Awaitable[str]]]) -> None:
        """Injectable completer for deterministic unit/integration testing."""
        self._llm_completer = fn

    def cancel_run(self, run_id: str) -> bool:
        """Flags an active benchmark run for immediate cancellation."""
        self.cancelled_runs.add(run_id)
        _logger.info(f"Cancellation requested for benchmark run '{run_id}'.")
        return True

    def is_cancelled(self, run_id: str) -> bool:
        return run_id in self.cancelled_runs

    async def _call_llm(
        self,
        model_name: str,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        num_ctx: int = 8192,
        timeout_seconds: float = 60.0
    ) -> str:
        """
        Invokes LLM backend (Ollama AsyncClient or injected test double).
        """
        if self._llm_completer:
            return await self._llm_completer(model_name, prompt, {
                "system": system_prompt,
                "temperature": temperature,
                "num_ctx": num_ctx,
                "timeout": timeout_seconds
            })

        # Real Ollama invocation wrapped in worker thread for Windows socket reliability
        from ollama import Client

        def _sync_chat() -> str:
            client = Client(timeout=max(300.0, timeout_seconds))
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat(
                model=model_name,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_ctx": num_ctx
                }
            )
            return response["message"]["content"]

        return await asyncio.to_thread(_sync_chat)

    def _extract_files_from_response(self, text: str, task: BenchmarkTask) -> Dict[str, str]:
        """
        Extracts code artifacts from model markdown fences and matches to required artifacts.
        """
        artifacts = global_code_extractor.extract_artifacts(text, default_language=task.language)
        files: Dict[str, str] = {}

        if not artifacts:
            # Check if raw text matches single expected artifact
            if len(task.required_artifacts) == 1:
                files[task.required_artifacts[0]] = text.strip()
            return files

        # Map by matching required artifact extensions or names
        req_arts = list(task.required_artifacts)
        for art in artifacts:
            target_name = art.filename
            # If target_name is a generic main_1.py, map to primary required artifact
            if req_arts and (art.filename.startswith("main_") or art.filename.startswith("index_")):
                target_name = req_arts.pop(0)
            files[target_name] = art.content

        # Fallback: if primary required artifact is still missing, assign first artifact content
        if task.required_artifacts:
            primary = task.required_artifacts[0]
            if primary not in files and artifacts:
                files[primary] = artifacts[0].content

        return files

    async def _execute_workflow_generation(
        self,
        task: BenchmarkTask,
        config: BenchmarkConfig,
        workdir: Path
    ) -> tuple[Dict[str, str], float, int, int]:
        """
        Executes the configured agent workflow (DIRECT, PLANNER_CODER, REVIEWED, or FULL_PIPELINE).
        Returns (generated_files, model_time_seconds, model_calls_count, repair_attempts_count).
        """
        t0 = time.perf_counter()
        model_calls = 0
        repair_attempts = 0

        # Construct task prompt
        task_prompt = f"Task: {task.name}\nDescription: {task.description}\nRequirements:\n"
        for req in task.requirements:
            task_prompt += f"- {req}\n"
        task_prompt += f"\nRequired output artifacts: {', '.join(task.required_artifacts)}\n"

        if task.initial_files:
            task_prompt += "\nInitial starting code provided:\n"
            for fn, cnt in task.initial_files.items():
                task_prompt += f"File: {fn}\n```python\n{cnt}\n```\n"

        system_instruction = (
            "You are an elite, deterministic AI software engineer. "
            "Generate production-grade code that satisfies all requirements. "
            "Format your response with standard markdown code blocks indicating file names."
        )

        workflow = config.workflow
        generated_code_text = ""

        if workflow == WorkflowType.DIRECT:
            # 1 single generation call
            direct_prompt = task_prompt + "\nPlease generate the required complete code files now."
            generated_code_text = await self._call_llm(
                model_name=config.model_name,
                prompt=direct_prompt,
                system_prompt=system_instruction,
                temperature=config.temperature,
                num_ctx=config.num_ctx,
                timeout_seconds=config.timeout_seconds
            )
            model_calls += 1

        elif workflow == WorkflowType.PLANNER_CODER:
            # Step 1: Planner
            plan_prompt = (
                f"{task_prompt}\nProvide a structured implementation plan and architectural breakdown."
            )
            plan_text = await self._call_llm(
                model_name=config.model_name,
                prompt=plan_prompt,
                system_prompt="You are a senior software architect creating an implementation plan.",
                temperature=config.temperature,
                timeout_seconds=config.timeout_seconds
            )
            model_calls += 1

            # Step 2: Coder
            coder_prompt = (
                f"{task_prompt}\n\nArchitecture Plan:\n{plan_text}\n\n"
                f"Now generate the final code files satisfying all requirements and the plan."
            )
            generated_code_text = await self._call_llm(
                model_name=config.model_name,
                prompt=coder_prompt,
                system_prompt=system_instruction,
                temperature=config.temperature,
                timeout_seconds=config.timeout_seconds
            )
            model_calls += 1

        elif workflow in (WorkflowType.PLANNER_CODER_REVIEWER, WorkflowType.FULL_PIPELINE):
            # Step 1: Planner
            plan_prompt = f"{task_prompt}\nCreate an implementation plan."
            plan_text = await self._call_llm(
                model_name=config.model_name,
                prompt=plan_prompt,
                system_prompt="You are a software architect.",
                temperature=config.temperature,
                timeout_seconds=config.timeout_seconds
            )
            model_calls += 1

            # Step 2: Coder
            coder_prompt = f"{task_prompt}\nPlan:\n{plan_text}\nGenerate code."
            initial_code = await self._call_llm(
                model_name=config.model_name,
                prompt=coder_prompt,
                system_prompt=system_instruction,
                temperature=config.temperature,
                timeout_seconds=config.timeout_seconds
            )
            model_calls += 1

            # Step 3: Reviewer
            if config.review_enabled:
                review_prompt = (
                    f"Review the following code for task '{task.name}':\n{initial_code}\n"
                    f"Requirements:\n{task_prompt}\n"
                    f"Identify any syntax errors, missed requirements, or edge-case bugs. Propose improvements."
                )
                review_notes = await self._call_llm(
                    model_name=config.model_name,
                    prompt=review_prompt,
                    system_prompt="You are a strict code reviewer checking for correctness and bugs.",
                    temperature=config.temperature,
                    timeout_seconds=config.timeout_seconds
                )
                model_calls += 1

                # Refinement step incorporating review
                refine_prompt = (
                    f"Refine and produce final code based on review feedback:\n{review_notes}\n"
                    f"Original code:\n{initial_code}\nOutput the polished code."
                )
                generated_code_text = await self._call_llm(
                    model_name=config.model_name,
                    prompt=refine_prompt,
                    system_prompt=system_instruction,
                    temperature=config.temperature,
                    timeout_seconds=config.timeout_seconds
                )
                model_calls += 1
            else:
                generated_code_text = initial_code

        # Extract files
        files = self._extract_files_from_response(generated_code_text, task)
        # Ensure any unchanged initial files are preserved if not re-generated
        for ifn, icnt in task.initial_files.items():
            if ifn not in files:
                files[ifn] = icnt

        # Self-repair loop for FULL_PIPELINE if testing enabled and max_repair_attempts > 0
        if workflow == WorkflowType.FULL_PIPELINE and config.testing_enabled and config.max_repair_attempts > 0:
            for attempt in range(config.max_repair_attempts):
                # Write current files to workdir to check against initial test files (if any)
                for fn, cnt in files.items():
                    (workdir / fn).write_text(cnt, encoding="utf-8")

                # If task has a test file in initial_files (like task 10), run it
                test_candidates = [f for f in files.keys() if f.startswith("test_") or f.endswith("_test.py")]
                if not test_candidates and task.initial_files:
                    test_candidates = [f for f in task.initial_files.keys() if f.startswith("test_")]

                if not test_candidates:
                    break  # No visible test file to self-heal against

                test_fn = test_candidates[0]
                run_test_cmd = [sys.executable, "-m", "pytest", test_fn, "-v"]
                sub = subprocess.run(run_test_cmd, cwd=str(workdir), capture_output=True, text=True, timeout=10.0)
                if sub.returncode == 0:
                    # Visible tests pass, no repair needed
                    break

                # Self-healing attempt
                repair_attempts += 1
                repair_prompt = (
                    f"Tests failed during execution attempt {attempt + 1}:\n"
                    f"Error output:\n{sub.stderr}\n{sub.stdout}\n\n"
                    f"Current code:\n{files.get(task.required_artifacts[0], '')}\n\n"
                    f"Fix the bug and provide the corrected code for {task.required_artifacts[0]}."
                )
                repaired_text = await self._call_llm(
                    model_name=config.model_name,
                    prompt=repair_prompt,
                    system_prompt="You are an expert self-repair debugger.",
                    temperature=config.temperature,
                    timeout_seconds=config.timeout_seconds
                )
                model_calls += 1
                repaired_files = self._extract_files_from_response(repaired_text, task)
                files.update(repaired_files)

        model_time = time.perf_counter() - t0
        return files, model_time, model_calls, repair_attempts

    def _run_validation(
        self,
        task: BenchmarkTask,
        workdir: Path,
        timeout_seconds: float
    ) -> tuple[int, str, str, float]:
        """
        Runs prescribed validation procedure out-of-band in an isolated environment.
        Writes hidden test files, executes pytest or syntax check, returns (exit_code, stdout, stderr, duration).
        """
        t0 = time.perf_counter()

        # 1. Write hidden validation test files into workdir
        for h_fname, h_content in task.hidden_test_files.items():
            (workdir / h_fname).write_text(h_content, encoding="utf-8")

        # 2. Determine validation command
        has_tests = bool(task.hidden_test_files) or any(
            p.name.startswith("test_") or p.name.endswith("_test.py") for p in workdir.glob("*.py")
        )

        if has_tests and task.language == "python":
            (workdir / "pytest.ini").write_text("[pytest]\ntestpaths = .\naddopts = -p no:cacheprovider\n", encoding="utf-8")
            # Model-generated code is untrusted: its tests run only in the Docker sandbox (no network,
            # non-root, resource limits), unless AIFORGE_TEST_SANDBOX=local explicitly allows the host.
            from backend.execution.docker_test_sandbox import run_pytest_in_docker, sandbox_mode, should_use_docker
            if sandbox_mode() != "local":
                if not should_use_docker():
                    return (NOT_RUN_EXIT_CODE, "", "Not run: generated code only runs in the Docker sandbox, and Docker "
                            "is not available. Start Docker, or set AIFORGE_TEST_SANDBOX=local to allow running it on "
                            "this machine.", round(time.perf_counter() - t0, 3))
                res = run_pytest_in_docker(workdir, timeout_seconds=max(60.0, timeout_seconds))
                return res.exit_code, res.stdout or "", res.stderr or "", round(time.perf_counter() - t0, 3)
            cmd = [sys.executable, "-m", "pytest", "-v", "-c", "pytest.ini"]
        elif task.language == "python":
            cmd = [sys.executable, "-m", "compileall", "."]    # byte-compiles only; nothing is executed
        else:
            # No automated validation exists for JavaScript/Markdown tasks: report it as not run, not passed.
            return (NOT_RUN_EXIT_CODE, "", f"Not run: no automated validation is implemented for {task.language} tasks.",
                    round(time.perf_counter() - t0, 3))

        # Build isolated environment without credentials
        clean_env = {
            k: v for k, v in os.environ.items()
            if not any(secret_key in k.upper() for secret_key in ("KEY", "SECRET", "PASSWORD", "TOKEN", "CREDENTIAL", "DATABASE_URL"))
        }
        clean_env["PYTHONPATH"] = str(workdir)
        clean_env["PYTHONDONTWRITEBYTECODE"] = "1"
        clean_env["PYTHONUNBUFFERED"] = "1"
        clean_env["TEMP"] = str(workdir)
        clean_env["TMP"] = str(workdir)

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(workdir),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=clean_env
            )
            duration = time.perf_counter() - t0
            return proc.returncode, proc.stdout or "", proc.stderr or "", round(duration, 3)
        except subprocess.TimeoutExpired:
            return -1, "", f"Validation timed out after {timeout_seconds} seconds.", round(time.perf_counter() - t0, 3)
        except Exception as e:
            return -1, "", f"Validation execution error: {e}", round(time.perf_counter() - t0, 3)

    async def execute_task_run(
        self,
        task: BenchmarkTask,
        config: BenchmarkConfig,
        run_id: str,
        iteration: int = 1
    ) -> TaskRunResult:
        """
        Executes a single task under a single configuration in total isolation.
        """
        result = TaskRunResult(
            task_id=task.id,
            task_name=task.name,
            config_id=config.id,
            run_iteration=iteration,
            start_time=datetime.now(timezone.utc).isoformat()
        )

        # Check model availability first
        if not config.is_available:
            result.status = "FAILED"
            result.error_message = config.availability_reason or f"Model '{config.model_name}' is unavailable."
            result.end_time = datetime.now(timezone.utc).isoformat()
            return result

        # Check for user cancellation
        if self.is_cancelled(run_id):
            result.status = "CANCELLED"
            result.error_message = "Benchmark run cancelled by user."
            result.end_time = datetime.now(timezone.utc).isoformat()
            return result

        # Isolated directory for this task execution
        task_workdir = RUNS_BASE_DIR / run_id / f"{task.id}_{config.id}_iter{iteration}"
        task_workdir.mkdir(parents=True, exist_ok=True)

        t_start_total = time.perf_counter()

        try:
            # 1. Initialize clean fixture files
            for fn, content in task.initial_files.items():
                (task_workdir / fn).write_text(content, encoding="utf-8")

            # 2. Acquire concurrency semaphore to protect host resources
            async with self.semaphore:
                if self.is_cancelled(run_id):
                    result.status = "CANCELLED"
                    result.error_message = "Benchmark run cancelled."
                    result.end_time = datetime.now(timezone.utc).isoformat()
                    return result

                # 3. Execute workflow code generation
                result.status = "RUNNING"
                gen_files, model_time, model_calls, repair_attempts = await self._execute_workflow_generation(
                    task=task,
                    config=config,
                    workdir=task_workdir
                )
                result.generated_files = gen_files

                # Write all generated files to workdir
                for fn, content in gen_files.items():
                    (task_workdir / fn).write_text(content, encoding="utf-8")

                # 4. Run out-of-band validation checks
                val_code, val_stdout, val_stderr, test_time = self._run_validation(
                    task=task,
                    workdir=task_workdir,
                    timeout_seconds=min(task.timeout_seconds, config.timeout_seconds)
                )

                result.validation_stdout = val_stdout[:100_000]
                result.validation_stderr = val_stderr[:50_000]
                if val_code == NOT_RUN_EXIT_CODE:
                    # Nothing was validated: no score is computed, and the result is not counted as a pass or fail.
                    result.status = "NOT_RUN"
                    result.error_message = val_stderr
                    return result

                total_duration = time.perf_counter() - t_start_total

                # 5. Objective Evaluation metrics
                metrics = global_objective_evaluator.evaluate_task_result(
                    task=task,
                    generated_files=gen_files,
                    exit_code=val_code,
                    stdout=val_stdout,
                    stderr=val_stderr,
                    duration_seconds=total_duration,
                    model_time_seconds=model_time,
                    test_time_seconds=test_time,
                    model_calls=model_calls,
                    repair_attempts=repair_attempts,
                    token_count=None,
                    regressions=0
                )
                result.metrics = metrics
                result.status = "COMPLETED" if val_code == 0 else "FAILED"

        except (asyncio.TimeoutError, TimeoutError):
            result.status = "TIMED_OUT"
            result.error_message = f"Execution exceeded timeout limit ({config.timeout_seconds}s)."
        except Exception as e:
            if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                result.status = "TIMED_OUT"
                result.error_message = f"Execution exceeded timeout limit: {e}"
            else:
                _logger.exception(f"Unhandled error in task execution '{task.id}': {e}")
                result.status = "FAILED"
                result.error_message = str(e)
        finally:
            result.end_time = datetime.now(timezone.utc).isoformat()

        return result

    async def execute_benchmark_suite(
        self,
        benchmark_run: BenchmarkRun,
        on_progress: Optional[Callable[[TaskRunResult], None]] = None
    ) -> BenchmarkRun:
        """
        Executes the complete benchmark matrix across selected configurations and tasks.
        Supports repeated runs and collects aggregate statistics.
        """
        benchmark_run.status = "RUNNING"
        tasks_to_run = [get_task_by_id(tid) for tid in benchmark_run.task_ids if get_task_by_id(tid)]
        if not tasks_to_run:
            tasks_to_run = ALL_BENCHMARK_TASKS

        iterations = max(1, benchmark_run.repeated_runs)

        for iteration in range(1, iterations + 1):
            for config in benchmark_run.configurations:
                for task in tasks_to_run:
                    if self.is_cancelled(benchmark_run.id):
                        benchmark_run.status = "CANCELLED"
                        break

                    task_result = await self.execute_task_run(
                        task=task,
                        config=config,
                        run_id=benchmark_run.id,
                        iteration=iteration
                    )
                    benchmark_run.results.append(task_result)

                    if on_progress:
                        on_progress(task_result)

                if self.is_cancelled(benchmark_run.id):
                    break
            if self.is_cancelled(benchmark_run.id):
                break

        if not self.is_cancelled(benchmark_run.id):
            benchmark_run.status = "COMPLETED"

        benchmark_run.completed_at = datetime.now(timezone.utc).isoformat()
        return benchmark_run


global_benchmark_engine = BenchmarkExecutionEngine()
