"""
AIForge Bounded Self-Debug Controller
======================================
Orchestrates bounded self-debugging loops for failing code artifacts.
Enforces MAX_SELF_DEBUG_ATTEMPTS = 2, early stop conditions (no progress, repeated error),
and candidate selection.
"""

import os
import logging
from typing import List, Tuple, Dict, Any

from backend.execution.models import (
    CodeArtifact,
    TestResult,
    FailureAnalysis,
    PatchResult,
    VerificationStatus
)
from backend.execution.sandbox_executor import global_sandbox_executor
from backend.execution.test_runner import global_test_runner
from backend.execution.failure_analyzer import global_failure_analyzer
from backend.execution.code_extractor import global_code_extractor
from backend.agents.coding_agent import global_coding_agent

_logger = logging.getLogger("aiforge.execution.self_debug")


class SelfDebugController:
    """
    Manages self-debugging loops for candidate code artifacts.
    """

    def debug_and_verify(
        self,
        user_prompt: str,
        initial_artifact: CodeArtifact,
        initial_test_res: TestResult
    ) -> Tuple[CodeArtifact, TestResult, VerificationStatus, int]:
        max_attempts = int(os.environ.get("AIFORGE_MAX_SELF_DEBUG_ATTEMPTS", "2"))

        # Rule 1: If initial run passed 100% tests -> VERIFIED
        if initial_test_res.passed > 0 and initial_test_res.failed == 0:
            return initial_artifact, initial_test_res, VerificationStatus.VERIFIED, 0

        # Rule 2: If infrastructure error -> EXECUTION_UNAVAILABLE
        if initial_test_res.execution_result and initial_test_res.execution_result.status.value == "INFRASTRUCTURE_ERROR":
            return initial_artifact, initial_test_res, VerificationStatus.EXECUTION_UNAVAILABLE, 0

        _logger.info(f"[SelfDebugController] Initial code failed tests (Passed: {initial_test_res.passed}/{initial_test_res.total}); starting bounded self-debug")

        candidates: List[Tuple[CodeArtifact, TestResult]] = [(initial_artifact, initial_test_res)]
        seen_code_hashes = {hash(initial_artifact.content.strip())}
        seen_error_fingerprints = set()

        current_art = initial_artifact
        current_test_res = initial_test_res

        attempts_used = 0

        for attempt in range(1, max_attempts + 1):
            attempts_used = attempt
            _logger.info(f"[SelfDebugController] Executing self-debug repair attempt {attempt}/{max_attempts}")

            # 1. Analyze failure
            analysis = global_failure_analyzer.analyze(current_test_res, current_art.content)
            fingerprint = f"{analysis.failure_type}:{analysis.summary}"

            # Early stop condition 1: Repeated identical failure fingerprint
            if fingerprint in seen_error_fingerprints:
                _logger.warning(f"[SelfDebugController] Repeated failure fingerprint '{fingerprint}' detected; stopping debug loop early")
                break
            seen_error_fingerprints.add(fingerprint)

            # 2. Generate minimal patch
            patch_prompt = (
                f"REQUIREMENT: {user_prompt}\n\n"
                f"CURRENT CODE:\n{current_art.content}\n\n"
                f"FAILURE ANALYSIS:\n- Type: {analysis.failure_type}\n- Summary: {analysis.summary}\n- Action: {analysis.action}\n\n"
                f"TASK: Fix the bug in the code. Preserve existing structure. Return ONLY corrected python/code block."
            )

            try:
                patch_out = global_coding_agent.process_coding_request(patch_prompt)
                raw_response = patch_out.get("response", current_art.content)
                extracted_arts = global_code_extractor.extract_artifacts(raw_response, current_art.language)
                patched_code = extracted_arts[0].content if extracted_arts else raw_response

                # Early stop condition 2: No-progress / identical code hash
                code_hash = hash(patched_code.strip())
                if code_hash in seen_code_hashes:
                    _logger.warning("[SelfDebugController] Patch generated identical code (No Progress); stopping debug loop early")
                    break
                seen_code_hashes.add(code_hash)

                patched_art = CodeArtifact(
                    filename=current_art.filename,
                    language=current_art.language,
                    content=patched_code,
                    purpose="SOURCE"
                )

                # 3. Re-run tests in sandbox
                new_test_res = global_test_runner.run_tests(patched_art, user_prompt)
                candidates.append((patched_art, new_test_res))

                current_art = patched_art
                current_test_res = new_test_res

                if new_test_res.passed > 0 and new_test_res.failed == 0:
                    _logger.info(f"[SelfDebugController] Self-debug attempt {attempt} SUCCESSFUL! All {new_test_res.passed} tests passed.")
                    return patched_art, new_test_res, VerificationStatus.VERIFIED, attempts_used

            except Exception as e:
                _logger.error(f"[SelfDebugController] Self-debug attempt {attempt} failed with exception: {e}")
                break

        # Best Candidate Selection: Pick candidate with highest passed test count
        best_art, best_test_res = max(candidates, key=lambda c: (c[1].passed, -c[1].failed))
        status = VerificationStatus.PARTIALLY_VERIFIED if best_test_res.passed > 0 else VerificationStatus.UNVERIFIED

        return best_art, best_test_res, status, attempts_used


global_self_debug_controller = SelfDebugController()
