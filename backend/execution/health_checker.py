"""
AIForge Health Checker Module
=============================
Performs empirical HTTP health checks against running application services.
Does NOT declare services 'RUNNING' or 'HEALTHY' without successful HTTP response validation.
"""

import time
import httpx
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

_logger = logging.getLogger("aiforge.execution.health_checker")


class HealthCheckResult(BaseModel):
    service_name: str
    is_healthy: bool
    status_code: int = 0
    url: str
    response_time_ms: float = 0.0
    error_message: Optional[str] = None


class HealthChecker:
    """
    HTTP Health probe for backend endpoints and frontend dev servers.
    """

    async def check_health_async(
        self,
        service_name: str,
        url: str,
        expected_status: int = 200,
        timeout_seconds: float = 2.0
    ) -> HealthCheckResult:
        start_t = time.time()
        try:
            async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
                res = await client.get(url)
                latency = round((time.time() - start_t) * 1000.0, 2)
                is_ok = (res.status_code == expected_status or (200 <= res.status_code < 400))

                return HealthCheckResult(
                    service_name=service_name,
                    is_healthy=is_ok,
                    status_code=res.status_code,
                    url=url,
                    response_time_ms=latency,
                    error_message=None if is_ok else f"Returned HTTP {res.status_code}"
                )
        except Exception as e:
            latency = round((time.time() - start_t) * 1000.0, 2)
            return HealthCheckResult(
                service_name=service_name,
                is_healthy=False,
                status_code=0,
                url=url,
                response_time_ms=latency,
                error_message=str(e)
            )

    async def wait_until_healthy(
        self,
        service_name: str,
        url: str,
        max_attempts: int = 15,
        interval_seconds: float = 1.0
    ) -> HealthCheckResult:
        _logger.info(f"HealthChecker: Waiting for '{service_name}' to become healthy at {url}...")
        last_res = None
        for attempt in range(max_attempts):
            last_res = await self.check_health_async(service_name, url)
            if last_res.is_healthy:
                _logger.info(f"HealthChecker: '{service_name}' is HEALTHY at {url} (attempt {attempt+1}/{max_attempts}, {last_res.response_time_ms}ms)")
                return last_res
            time.sleep(interval_seconds)

        _logger.warning(f"HealthChecker: '{service_name}' health check failed at {url} after {max_attempts} attempts: {last_res.error_message if last_res else 'timeout'}")
        return last_res or HealthCheckResult(
            service_name=service_name,
            is_healthy=False,
            url=url,
            error_message="Timed out waiting for server startup"
        )


global_health_checker = HealthChecker()
