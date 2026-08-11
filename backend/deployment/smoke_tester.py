"""
AIForge Deployment Smoke Tester Module
======================================
Executes lightweight empirical post-deployment HTTP smoke tests.
Ensures application routes respond correctly before marking deployment VERIFIED.
"""

import time
import httpx
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

_logger = logging.getLogger("aiforge.deployment.smoke_tester")


class SmokeTestCase(BaseModel):
    name: str
    passed: bool
    status_code: int = 0
    duration_ms: float = 0.0
    error_message: Optional[str] = None


class SmokeTestResult(BaseModel):
    passed: bool
    total: int
    passed_count: int
    failed_count: int
    cases: List[SmokeTestCase] = Field(default_factory=list)


class SmokeTester:
    """
    Post-deployment HTTP smoke testing engine.
    """

    async def run_smoke_tests_async(
        self,
        frontend_url: str,
        backend_url: str
    ) -> SmokeTestResult:
        _logger.info(f"SmokeTester: Probing deployed application at FE={frontend_url}, BE={backend_url}...")
        cases = []

        async with httpx.AsyncClient(timeout=4.0, follow_redirects=True) as client:
            # 1. Homepage GET
            t0 = time.time()
            try:
                res = await client.get(frontend_url)
                ok = (res.status_code == 200)
                cases.append(SmokeTestCase(
                    name="GET / (Homepage)",
                    passed=ok,
                    status_code=res.status_code,
                    duration_ms=round((time.time() - t0) * 1000, 2),
                    error_message=None if ok else f"HTTP {res.status_code}"
                ))
            except Exception as e:
                cases.append(SmokeTestCase(
                    name="GET / (Homepage)",
                    passed=False,
                    duration_ms=round((time.time() - t0) * 1000, 2),
                    error_message=str(e)
                ))

            # 2. Backend Health GET
            t0 = time.time()
            try:
                res = await client.get(f"{backend_url}/health")
                ok = (res.status_code == 200)
                cases.append(SmokeTestCase(
                    name="GET /health (API Probe)",
                    passed=ok,
                    status_code=res.status_code,
                    duration_ms=round((time.time() - t0) * 1000, 2),
                    error_message=None if ok else f"HTTP {res.status_code}"
                ))
            except Exception as e:
                cases.append(SmokeTestCase(
                    name="GET /health (API Probe)",
                    passed=False,
                    duration_ms=round((time.time() - t0) * 1000, 2),
                    error_message=str(e)
                ))

            # 3. Auth Endpoint POST
            t0 = time.time()
            try:
                res = await client.post(f"{backend_url}/api/auth/login", json={"email": "admin@aiforge.io", "password": "admin123"})
                ok = (res.status_code == 200)
                cases.append(SmokeTestCase(
                    name="POST /api/auth/login (Auth Endpoint)",
                    passed=ok,
                    status_code=res.status_code,
                    duration_ms=round((time.time() - t0) * 1000, 2),
                    error_message=None if ok else f"HTTP {res.status_code}"
                ))
            except Exception as e:
                cases.append(SmokeTestCase(
                    name="POST /api/auth/login (Auth Endpoint)",
                    passed=False,
                    duration_ms=round((time.time() - t0) * 1000, 2),
                    error_message=str(e)
                ))

        passed_cnt = sum(1 for c in cases if c.passed)
        failed_cnt = len(cases) - passed_cnt

        return SmokeTestResult(
            passed=(failed_cnt == 0),
            total=len(cases),
            passed_count=passed_cnt,
            failed_count=failed_cnt,
            cases=cases
        )


global_smoke_tester = SmokeTester()
