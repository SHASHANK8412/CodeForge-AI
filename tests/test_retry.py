import asyncio
import pytest
from backend.utils.retry import async_retry, get_retry_stats, reset_retry_stats


@pytest.mark.anyio
async def test_retry_success_after_failures():
    reset_retry_stats()
    attempts = 0

    @async_retry(retries=3, initial_delay=0.01, backoff_factor=1.5, timeout=5.0)
    async def failing_action():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ConnectionError("Temporary connection failure")
        return "success"

    result = await failing_action()
    assert result == "success"
    assert attempts == 2
    assert get_retry_stats() == 1


@pytest.mark.anyio
async def test_retry_exceeds_max_retries():
    reset_retry_stats()

    @async_retry(retries=2, initial_delay=0.01, backoff_factor=1.5, timeout=5.0)
    async def always_fails():
        raise ConnectionError("Persistent temporary failure")

    with pytest.raises(ConnectionError):
        await always_fails()

    assert get_retry_stats() == 1


@pytest.mark.anyio
async def test_retry_permanent_error():
    reset_retry_stats()

    @async_retry(retries=3, initial_delay=0.01, backoff_factor=1.5, timeout=5.0)
    async def permanent_fail():
        raise ValueError("Permanent invalid argument")

    with pytest.raises(ValueError):
        await permanent_fail()

    # ValueError is permanent, so it shouldn't retry
    assert get_retry_stats() == 0


@pytest.mark.anyio
async def test_retry_timeout_trigger():
    reset_retry_stats()

    @async_retry(retries=2, initial_delay=0.01, backoff_factor=1.5, timeout=0.02)
    async def slow_action():
        await asyncio.sleep(1.0)
        return "slow"

    with pytest.raises(asyncio.TimeoutError):
        await slow_action()
