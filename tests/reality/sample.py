"""
Reality Simulator sample: a FastAPI app whose endpoints burn a known amount of CPU (so its capacity is
predictable in principle) and one endpoint that calls an external payments service (PAYMENTS_URL).
"""

from pathlib import Path

MAIN = '''import json
import os
import urllib.request

from fastapi import FastAPI

app = FastAPI()


def burn(units):
    # a fixed amount of CPU work (not a wall-clock wait), so a CPU limit really slows it down
    return sum(i * i for i in range(units))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/compute")
def compute():
    burn(400_000)
    return {"ok": True}


@app.get("/api/light")
def light():
    burn(25_000)
    return {"ok": True}


@app.get("/api/checkout")
def checkout():
    url = os.environ.get("PAYMENTS_URL", "http://payments:8080")
    with urllib.request.urlopen(url + "/charge", timeout=5) as response:
        data = json.loads(response.read())
    return {"charged": bool(data.get("ok"))}
'''

TESTS = '''from fastapi.testclient import TestClient

from backend.main import app


def test_compute():
    assert TestClient(app).get("/api/compute").json() == {"ok": True}
'''


def write_sample(path) -> Path:
    root = Path(path)
    for rel, content in {"backend/main.py": MAIN, "tests/test_app.py": TESTS, "requirements.txt": "fastapi\nhttpx\n"}.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(content, encoding="utf-8")
    return root
