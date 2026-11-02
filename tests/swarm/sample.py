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


# --- v2: a typed contract (JSON Schema subset) and component variants for the contract-aware tests ----------------

ORDER = {"type": "object", "properties": {"id": {"type": "integer"}, "item": {"type": "string"}, "quantity": {"type": "integer"}},
         "required": ["id", "item", "quantity"]}
CONTRACT_V2 = Contract(name="orders", endpoints=[
    Endpoint(method="POST", path="/api/orders", description="create an order",
             request_schema={"type": "object", "properties": {"item": {"type": "string"}, "quantity": {"type": "integer", "minimum": 1}},
                             "required": ["item", "quantity"]},
             responses={"201": {"content_type": "application/json", "schema": ORDER}},
             errors={"422": {"content_type": "application/json", "description": "invalid order"}}),
    Endpoint(method="GET", path="/api/orders/{order_id}", description="read an order", path_params={"order_id": {"type": "integer"}},
             responses={"200": {"content_type": "application/json", "schema": ORDER}},
             errors={"404": {"content_type": "application/json", "description": "unknown order"},
                     "422": {"content_type": "application/json", "description": "invalid id"}}),
])

BACKEND_V2 = BACKEND.replace('@app.post("/api/orders")', '@app.post("/api/orders", status_code=201)')
BACKEND_V2_TESTS = BACKEND_TESTS
# each departs from CONTRACT_V2 in exactly one way
BACKEND_V2_STATUS_200 = BACKEND                                                    # POST answers 200, not 201
BACKEND_V2_TEXT = BACKEND_V2.replace("from fastapi import FastAPI, HTTPException",
                                     "from fastapi import FastAPI, HTTPException\nfrom fastapi.responses import PlainTextResponse").replace(
    '''        raise HTTPException(status_code=404, detail="order not found")
    return ORDERS[order_id]''', '''        raise HTTPException(status_code=404, detail="order not found")
    return PlainTextResponse(str(ORDERS[order_id]))''')           # GET answers text/plain
BACKEND_V2_MISSING_FIELD = BACKEND_V2.replace(
    '''detail="order not found")
    return ORDERS[order_id]
''', '''detail="order not found")
    return {"id": order_id, "item": ORDERS[order_id]["item"]}
''')                                                                 # GET omits quantity
BACKEND_V2_WRONG_TYPE = BACKEND_V2.replace(
    '''    ORDERS[order_id] = {"id": order_id, "item": order.item, "quantity": order.quantity}''',
    '''    ORDERS[order_id] = {"id": str(order_id), "item": order.item, "quantity": order.quantity}''').replace(
    "    if order_id not in ORDERS:", "    if order_id not in ORDERS and str(order_id) not in [o['id'] for o in ORDERS.values()]:").replace(
    "    return ORDERS[order_id]\n", "    return ORDERS.get(order_id) or next(o for o in ORDERS.values() if o['id'] == str(order_id))\n")   # id is a string
BACKEND_V2_LIST = BACKEND_V2.replace('not found")\n    return ORDERS[order_id]\n', 'not found")\n    return [ORDERS[order_id]]\n')       # GET answers a list
BACKEND_V2_INSECURE = BACKEND_V2.replace("from fastapi import FastAPI, HTTPException",
                                         "import subprocess\n\nfrom fastapi import FastAPI, HTTPException").replace(
    "    order_id = len(ORDERS) + 1\n",
    "    order_id = len(ORDERS) + 1\n    subprocess.run(\"echo \" + order.item, shell=True)\n")   # a repair that adds command injection

CLIENT_V2 = '''const API = import.meta.env.VITE_API_URL || "";

export async function createOrder(item, qty) {
  const response = await fetch(`${API}/api/orders`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ item, quantity: qty }),
  });
  if (!response.ok) throw new Error(`createOrder failed: ${response.status}`);
  return response.json();
}

export async function getOrder(id) {
  const response = await fetch(`${API}/api/orders/${id}`);
  if (!response.ok) throw new Error(`getOrder failed: ${response.status}`);
  return response.json();
}
'''
CLIENT_V2_WRONG = CLIENT_WRONG                                      # POST /api/order with {item, qty}
CLIENT_V2_STRING_QTY = CLIENT_V2.replace("quantity: qty }", "quantity: String(qty) }")   # quantity sent as a string
CLIENT_V2_THROWS = CLIENT_V2.replace("  return response.json();\n}\n\nexport async function getOrder",
                                     "  const data = await response.json();\n  return data.order.id;\n}\n\nexport async function getOrder")


def staged_agents(backend=(BACKEND_V2,), client=(CLIENT_V2,), tests=BACKEND_V2_TESTS):
    """Fixed agent answers by attempt: the n-th request to an agent gets the n-th version (the last one repeats).
    Requests are counted in generate.calls; the requests themselves are kept in generate.prompts."""
    calls = {"backend": 0, "frontend": 0}
    prompts = {"backend": [], "frontend": []}

    def generate(system, prompt):
        if "Agent: backend_agent" in prompt:
            calls["backend"] += 1
            prompts["backend"].append(prompt)
            code = backend[min(calls["backend"], len(backend)) - 1]
            return f"### backend/main.py\n```python\n{code}```\n### backend/tests/test_orders.py\n```python\n{tests}```\n"
        if "Agent: frontend_agent" in prompt:
            calls["frontend"] += 1
            prompts["frontend"].append(prompt)
            code = client[min(calls["frontend"], len(client)) - 1]
            return f"### frontend/src/api/client.js\n```javascript\n{code}```\n"
        return "no change"
    generate.calls = calls
    generate.prompts = prompts
    return generate
