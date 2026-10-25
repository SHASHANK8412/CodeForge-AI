"""
Every (method, path) has exactly one handler.

With two routers on the same path only the first registered ever runs; the other is dead code
that looks live. That hid real bugs: the engineering-memory pages got another router's response,
the upload box hit the RAG router (different form field), and /health had two fake handlers.
"""
from collections import defaultdict

from backend.main import app


def _routes():
    for r in app.router.routes:
        if type(r).__name__ == "_IncludedRouter":
            for ctx in r.effective_route_contexts():
                yield ctx.path, ctx.methods or set(), ctx.endpoint
        elif hasattr(r, "methods") and hasattr(r, "endpoint"):
            yield r.path, r.methods or set(), r.endpoint


def test_no_two_handlers_share_a_route():
    owners = defaultdict(set)
    for path, methods, endpoint in _routes():
        for method in methods - {"HEAD", "OPTIONS"}:
            owners[(method, path)].add(f"{endpoint.__module__}.{endpoint.__qualname__}")
    duplicates = {f"{m} {p}": sorted(e) for (m, p), e in owners.items() if len(e) > 1}
    assert duplicates == {}


def test_health_reports_real_checks():
    from fastapi.testclient import TestClient
    body = TestClient(app).get("/health").json()
    assert body["status"] == "healthy" and body["services"]["api"] == "up"
    assert body["services"]["ollama"] in ("up", "down", "error")
    assert body["services"]["docker_sandbox"] in ("up", "down")
