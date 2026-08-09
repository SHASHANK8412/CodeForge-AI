"""
AIForge Quality Recovery Day 14 — Resilience, Retries, Circuit Breaker & Fallbacks
===================================================================================
Provides centralized RetryPolicy (transient retries only), CircuitBreaker 
(CLOSED, OPEN, HALF_OPEN state machine), and FallbackPolicy for graceful degradation.
"""

import time
import random
import logging
from typing import Callable, Any, Optional, Dict, Tuple

from backend.performance.models import CircuitState, ErrorCategory
from backend.performance.config import global_performance_config

logger = logging.getLogger("aiforge.performance.resilience")


class RetryPolicy:
    """
    Centralized retry policy enforcing exponential backoff and transient-only error retries.
    """

    TRANSIENT_ERRORS = (
        "TimeoutError",
        "ConnectionError",
        "HTTPError",
        "ServiceUnavailable",
        "RateLimitError",
        "503",
        "502",
        "504"
    )

    NON_RETRYABLE_ERRORS = (
        "SyntaxError",
        "ValueError",
        "FileNotFoundError",
        "PermissionError",
        "ValidationError",
        "SecurityBlockError"
    )

    def is_retryable(self, error: Exception) -> bool:
        """Determines if an exception is transient and safe to retry."""
        err_name = type(error).__name__
        err_str = str(error)

        if any(non in err_name or non in err_str for non in self.NON_RETRYABLE_ERRORS):
            return False

        if any(trans in err_name or trans in err_str for trans in self.TRANSIENT_ERRORS):
            return True

        # Default: network/timeout/connection issues are retryable
        return isinstance(error, (TimeoutError, ConnectionError, OSError))

    def execute_with_retry(
        self,
        func: Callable[..., Any],
        *args,
        max_retries: Optional[int] = None,
        stage_name: str = "OPERATION",
        **kwargs
    ) -> Any:
        """Executes a function with bounded exponential backoff retries."""
        limit = max_retries if max_retries is not None else global_performance_config.MAX_RETRIES
        delay = global_performance_config.RETRY_INITIAL_DELAY_SECONDS

        for attempt in range(1, limit + 1):
            try:
                return func(*args, **kwargs)
            except Exception as ex:
                if not self.is_retryable(ex) or attempt == limit:
                    logger.warning(f"[{stage_name}] Non-retryable failure or retry budget exhausted on attempt {attempt}/{limit}: {ex}")
                    raise ex

                jitter = random.uniform(0.8, 1.2)
                sleep_time = min(delay * jitter, global_performance_config.RETRY_MAX_DELAY_SECONDS)
                logger.info(f"[{stage_name}] Transient failure on attempt {attempt}/{limit}: {ex}. Retrying in {sleep_time:.2f}s...")
                time.sleep(sleep_time)
                delay *= 2.0


class CircuitBreaker:
    """
    Circuit breaker for external or unstable service dependencies.
    States: CLOSED -> (failures >= threshold) -> OPEN -> (cooldown) -> HALF_OPEN -> CLOSED
    """

    def __init__(self, name: str, failure_threshold: int = 3, recovery_seconds: float = 10.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_state_change = time.time()

    def allow_request(self) -> bool:
        """Checks if a request should be permitted through the circuit."""
        now = time.time()

        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if now - self.last_state_change >= self.recovery_seconds:
                logger.info(f"CircuitBreaker[{self.name}]: OPEN -> HALF_OPEN recovery probe initiated.")
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = now
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            return True

        return True

    def record_success(self) -> None:
        """Records a successful operation, resetting the circuit to CLOSED."""
        if self.state != CircuitState.CLOSED:
            logger.info(f"CircuitBreaker[{self.name}]: Operation succeeded! Resetting state to CLOSED.")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_state_change = time.time()

    def record_failure(self) -> None:
        """Records a failure. Opens circuit if failure threshold is reached."""
        self.failure_count += 1
        now = time.time()

        if self.state == CircuitState.HALF_OPEN:
            logger.warning(f"CircuitBreaker[{self.name}]: Half-open probe failed! Tripping back to OPEN.")
            self.state = CircuitState.OPEN
            self.last_state_change = now
        elif self.failure_count >= self.failure_threshold:
            logger.warning(f"CircuitBreaker[{self.name}]: {self.failure_count} consecutive failures! Tripping to OPEN.")
            self.state = CircuitState.OPEN
            self.last_state_change = now


class CircuitBreakerRegistry:
    """Registry maintaining circuit breakers for all subsystem dependencies."""

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {
            "ollama": CircuitBreaker("ollama"),
            "vector_db": CircuitBreaker("vector_db"),
            "embedding_service": CircuitBreaker("embedding_service"),
            "github_api": CircuitBreaker("github_api"),
        }

    def get(self, name: str) -> CircuitBreaker:
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name)
        return self._breakers[name]


class FallbackPolicy:
    """Defines graceful degradation fallbacks when dependencies fail."""

    def execute_with_fallback(
        self,
        primary_func: Callable[..., Any],
        fallback_func: Callable[..., Any],
        circuit_name: Optional[str] = None
    ) -> Tuple[Any, bool]:
        """
        Executes primary_func. If circuit is OPEN or primary fails, calls fallback_func.
        Returns: (result, is_degraded)
        """
        cb = global_circuit_breaker_registry.get(circuit_name) if circuit_name else None

        if cb and not cb.allow_request():
            logger.warning(f"Circuit[{circuit_name}] is OPEN. Executing fallback path immediately.")
            return fallback_func(), True

        try:
            res = primary_func()
            if cb:
                cb.record_success()
            return res, False
        except Exception as ex:
            if cb:
                cb.record_failure()
            logger.warning(f"Primary operation failed ({ex}). Executing fallback path.")
            return fallback_func(), True


global_retry_policy = RetryPolicy()
global_circuit_breaker_registry = CircuitBreakerRegistry()
global_fallback_policy = FallbackPolicy()
