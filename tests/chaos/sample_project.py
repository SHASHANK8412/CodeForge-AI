"""
A small FastAPI shop that depends on an inventory service (URL from INVENTORY_URL), written the way
generated apps often are: the outbound call has no timeout and no error handling. Used to verify the
Chaos Engineer against real failures. write_sample(path) writes it as a project folder.
(A module rather than files, so pytest never collects the sample's own tests as AIForge tests.)
"""

from pathlib import Path

MAIN = '''import json
import os
import urllib.request

from fastapi import FastAPI

INVENTORY_URL = os.environ.get("INVENTORY_URL", "http://inventory:8080")
PRODUCTS = [{"sku": "A1", "name": "Lamp"}, {"sku": "B2", "name": "Desk"}, {"sku": "C3", "name": "Chair"}]

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/catalog")
def catalog():
    return {"count": len(PRODUCTS), "products": [p["name"] for p in PRODUCTS]}


def fetch_stock():
    with urllib.request.urlopen(INVENTORY_URL + "/stock") as resp:
        return json.loads(resp.read())


@app.get("/api/products")
def products():
    stock = fetch_stock()
    return [{**p, "stock": stock.get(p["sku"])} for p in PRODUCTS]
'''

TESTS = '''from unittest.mock import patch

from fastapi.testclient import TestClient

from backend import main

client = TestClient(main.app)


def test_products_include_stock():
    with patch.object(main, "fetch_stock", return_value={"A1": 5, "B2": 0, "C3": 2}):
        body = client.get("/api/products").json()
    assert [p["sku"] for p in body] == ["A1", "B2", "C3"]
    assert body[0]["stock"] == 5 and body[1]["stock"] == 0


def test_catalog():
    assert client.get("/api/catalog").json()["count"] == 3
'''

FILES = {
    "backend/main.py": MAIN,
    "requirements.txt": "fastapi\nhttpx\n",
    "tests/test_shop.py": TESTS,
}

INVENTORY_ROUTES = {"/stock": {"A1": 5, "B2": 0, "C3": 2}}


def write_sample(path) -> Path:
    root = Path(path)
    for rel, content in FILES.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return root
