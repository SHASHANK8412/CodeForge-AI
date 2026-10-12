"""
Swarm Intelligence sample: a tiny FastAPI project and an orders API contract, plus fixed agent answers used in
place of the local coding model in tests. The frontend agent's first answer departs from the contract (wrong
path and field name); after the Integration Agent's feedback it follows the contract.
"""

from pathlib import Path

from backend.swarm.models import Contract, Endpoint

BASE = {
    "backend/main.py": '''from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}
''',
    "tests/test_health.py": '''from fastapi.testclient import TestClient

from backend.main import app


def test_health():
    assert TestClient(app).get("/health").json() == {"status": "ok"}
''',
    "requirements.txt": "fastapi\nhttpx\n",
    "frontend/package.json": '{"name": "shop-ui", "private": true}\n',
}

CONTRACT = Contract(name="orders", endpoints=[
    Endpoint(method="POST", path="/api/orders", request_fields=["item", "quantity"], response_fields=["id", "item", "quantity"],
             description="create an order"),
    Endpoint(method="GET", path="/api/orders/{order_id}", response_fields=["id", "item", "quantity"], description="read an order"),
])

BACKEND = '''from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
ORDERS = {}


class OrderIn(BaseModel):
    item: str
    quantity: int = 1


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/orders")
def create_order(order: OrderIn):
    order_id = len(ORDERS) + 1
    ORDERS[order_id] = {"id": order_id, "item": order.item, "quantity": order.quantity}
    return ORDERS[order_id]


@app.get("/api/orders/{order_id}")
def get_order(order_id: int):
    if order_id not in ORDERS:
        raise HTTPException(status_code=404, detail="order not found")
    return ORDERS[order_id]
'''

BACKEND_TESTS = '''from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_create_and_read_an_order():
    created = client.post("/api/orders", json={"item": "pizza", "quantity": 2}).json()
    assert created["item"] == "pizza" and created["quantity"] == 2
    assert client.get(f"/api/orders/{created['id']}").json() == created
'''

CLIENT_WRONG = '''const API = import.meta.env.VITE_API_URL || "";

export async function createOrder(item, qty) {
  const response = await fetch(`${API}/api/order`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ item, qty }),
  });
  return response.json();
}

export async function getOrder(id) {
  const response = await fetch(`${API}/api/orders/${id}`);
  return response.json();
}
'''

CLIENT_FIXED = CLIENT_WRONG.replace("/api/order`", "/api/orders`").replace("item, qty }", "item, quantity: qty }")


def write_sample(path) -> Path:
    root = Path(path)
    for rel, content in BASE.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(content, encoding="utf-8")
    return root


def scripted_agents(frontend_fixes_on_feedback=True, backend=None):
    """Answers keyed by the agent named in the request; a frontend request that carries feedback gets the fix."""
    calls = {"backend": 0, "frontend": 0}

    def generate(system, prompt):
        if "Agent: backend_agent" in prompt:
            calls["backend"] += 1
            return (f"### backend/main.py\n```python\n{backend or BACKEND}```\n"
                    f"### backend/tests/test_orders.py\n```python\n{BACKEND_TESTS}```\n")
        if "Agent: frontend_agent" in prompt:
            calls["frontend"] += 1
            fixed = frontend_fixes_on_feedback and "previous attempt was rejected" in prompt
            return f"### frontend/src/api/client.js\n```javascript\n{CLIENT_FIXED if fixed else CLIENT_WRONG}```\n"
        return "no change"
    generate.calls = calls
    return generate
