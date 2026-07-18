import asyncio
import functools
import logging
from typing import Any, Callable

_logger = logging.getLogger("aiforge.performance")

# Global counter to keep track of retries used during workflow execution
retries_used_count = 0


def reset_retry_stats() -> None:
    global retries_used_count
    retries_used_count = 0


def get_retry_stats() -> int:
    return retries_used_count


def async_retry(
    retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    timeout: float | None = 30.0,
) -> Callable:
    """
    Decorator for retrying async functions upon encountering temporary exceptions.
    Applies exponential backoff and sets a timeout.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            global retries_used_count
            delay = initial_delay
            last_exc = None

            for attempt in range(1, retries + 1):
                try:
                    if timeout is not None:
                        # Apply timeout to the async execution
                        return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
                    return await func(*args, **kwargs)
                except (asyncio.TimeoutError, ConnectionError) as exc:
                    last_exc = exc
                    _logger.warning("INFO Retry Attempt %d - Timeout/Connection error: %s", attempt, exc)
                except Exception as exc:  # noqa: BLE001
                    # Identify if it is a temporary HTTP/Ollama exception
                    # Ollama ResponseError has status_code attribute.
                    # 429 (Rate limit) or 5xx (Server error) are transient
                    status_code = getattr(exc, "status_code", None)
                    error_msg = str(exc).lower()
                    
                    is_transient = (
                        status_code in {429, 500, 502, 503, 504}
                        or "timeout" in error_msg
                        or "connection" in error_msg
                        or "rate limit" in error_msg
                        or "too many requests" in error_msg
                    )
                    
                    if not is_transient:
                        # Re-raise permanent failures immediately
                        _logger.error("Permanent LLM failure detected: %s", exc)
                        raise exc
                    
                    last_exc = exc
                    _logger.warning("INFO Retry Attempt %d - Transient error: %s", attempt, exc)

                if attempt < retries:
                    retries_used_count += 1
                    _logger.info("INFO Sleeping %.1fs before retry...", delay)
                    await asyncio.sleep(delay)
                    delay *= backoff_factor

            _logger.error("All %d retry attempts failed. Raising last exception.", retries)
            if last_exc is not None:
                raise last_exc
            raise RuntimeError("Unknown retry error")

        return wrapper
    return decorator
