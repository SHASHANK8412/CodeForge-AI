"""
AIForge Benchmark Lab — Task Library
====================================
Contains the official suite of 10 deterministic benchmark tasks with objective
acceptance criteria, fixtures, and out-of-band validation test suites.
"""

from typing import Dict, List, Optional
from backend.benchmark_lab.models import (
    BenchmarkTask,
    TaskCategory,
    TaskDifficulty,
)


TASK_01_URL_PARSER = BenchmarkTask(
    id="task_01_py_utility",
    name="Python Utility with Comprehensive Tests",
    description="Implement a URL query string parser and serializer utility 'url_utils.py' with parsing, dictionary conversion, array handling, and encoding support.",
    category=TaskCategory.GENERATION,
    difficulty=TaskDifficulty.EASY,
    language="python",
    framework="pytest",
    template="python-utility",
    requirements=[
        "Implement `parse_query_string(query: str) -> dict` in url_utils.py",
        "Implement `build_query_string(params: dict) -> str` in url_utils.py",
        "Properly handle URL percent encoding and decoding for special characters",
        "Support multi-value keys by returning a list of values",
        "Handle empty strings and queries starting with '?' gracefully"
    ],
    required_artifacts=["url_utils.py"],
    acceptance_criteria=[
        "url_utils.py defines parse_query_string and build_query_string",
        "Special characters (e.g., spaces as '%20' or '+', '&', '=') are correctly handled",
        "Multi-value keys parsed into lists or normalized",
        "Passes all hidden validation tests"
    ],
    timeout_seconds=20.0,
    initial_files={},
    validation_procedure="pytest",
    hidden_test_files={
        "test_hidden_url_utils.py": """
import pytest
from url_utils import parse_query_string, build_query_string

def test_parse_basic():
    res = parse_query_string("name=Alice&age=30")
    assert res.get("name") == "Alice"
    assert res.get("age") == "30"

def test_parse_with_leading_question_mark():
    res = parse_query_string("?search=machine%20learning&limit=10")
    assert res.get("search") == "machine learning"
    assert res.get("limit") == "10"

def test_parse_empty():
    assert parse_query_string("") == {}
    assert parse_query_string("?") == {}

def test_build_basic():
    qs = build_query_string({"filter": "active", "page": 1})
    assert "filter=active" in qs
    assert "page=1" in qs

def test_roundtrip_encoding():
    params = {"query": "hello world!", "tag": "ai&ml"}
    encoded = build_query_string(params)
    decoded = parse_query_string(encoded)
    assert decoded.get("query") == "hello world!"
    assert decoded.get("tag") == "ai&ml"
"""
    }
)

TASK_02_FASTAPI_CRUD = BenchmarkTask(
    id="task_02_fastapi_crud",
    name="FastAPI CRUD Application",
    description="Implement a modular FastAPI service in 'main.py' managing an in-memory catalog of Items with GET, POST, DELETE, and error handling.",
    category=TaskCategory.GENERATION,
    difficulty=TaskDifficulty.MEDIUM,
    language="python",
    framework="fastapi",
    template="fastapi-standard",
    requirements=[
        "Create FastAPI app with endpoints for Items catalog",
        "GET /items: returns list of all items",
        "POST /items: creates a new item with 'name', 'price', and optional 'description'",
        "GET /items/{item_id}: returns item or HTTP 404 if not found",
        "DELETE /items/{item_id}: removes item or HTTP 404 if not found",
        "Use Pydantic schema validation for item creation"
    ],
    required_artifacts=["main.py"],
    acceptance_criteria=[
        "FastAPI app instance named 'app' in main.py",
        "Pydantic ItemCreate and Item models defined",
        "HTTP 201 status code on successful item creation",
        "HTTP 404 returned on missing item lookups",
        "Passes hidden test suite"
    ],
    timeout_seconds=30.0,
    initial_files={},
    validation_procedure="pytest",
    hidden_test_files={
        "test_hidden_fastapi.py": """
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_crud_lifecycle():
    # 1. List initially empty or list
    res = client.get("/items")
    assert res.status_code == 200
    initial_count = len(res.json())

    # 2. Create item
    payload = {"name": "Test Gadget", "price": 49.99, "description": "High quality gadget"}
    create_res = client.post("/items", json=payload)
    assert create_res.status_code in [200, 201]
    created = create_res.json()
    assert created["name"] == "Test Gadget"
    item_id = created.get("id", 1)

    # 3. Get item by id
    get_res = client.get(f"/items/{item_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Test Gadget"

    # 4. 404 on invalid ID
    missing_res = client.get("/items/999999")
    assert missing_res.status_code == 404

    # 5. Delete item
    del_res = client.delete(f"/items/{item_id}")
    assert del_res.status_code in [200, 204]

    # Verify deleted
    verify_res = client.get(f"/items/{item_id}")
    assert verify_res.status_code == 404
"""
    }
)

TASK_03_REACT_FRONTEND = BenchmarkTask(
    id="task_03_react_frontend",
    name="React Frontend API Consumer Component",
    description="Implement a React component 'TaskList.jsx' that fetches tasks from '/api/tasks', manages loading/error states, and allows toggling task completion.",
    category=TaskCategory.GENERATION,
    difficulty=TaskDifficulty.MEDIUM,
    language="javascript",
    framework="react",
    template="react-component",
    requirements=[
        "Create React functional component 'TaskList'",
        "Manage useState for tasks list, loading status, and error message",
        "Fetch tasks on component mount using useEffect",
        "Render loading spinner/indicator when loading is true",
        "Render error alert when fetching fails",
        "Provide button/checkbox to toggle completion status"
    ],
    required_artifacts=["TaskList.jsx"],
    acceptance_criteria=[
        "TaskList.jsx exports default React component",
        "Handles loading and error states cleanly",
        "Includes toggle action handler",
        "No syntax errors and adheres to React hooks rules"
    ],
    timeout_seconds=20.0,
    initial_files={},
    validation_procedure="syntax_and_ast",
    hidden_test_files={}
)

TASK_04_DB_SCHEMA = BenchmarkTask(
    id="task_04_db_schema",
    name="Database Schema and Data Models",
    description="Define SQLAlchemy relational database models in 'models.py' for an e-commerce platform: User, Order, and OrderItem with relationships and foreign keys.",
    category=TaskCategory.GENERATION,
    difficulty=TaskDifficulty.MEDIUM,
    language="python",
    framework="sqlalchemy",
    template="sqlalchemy-models",
    requirements=[
        "Define declarative base models in 'models.py'",
        "User model: id (PK), email (unique), username, created_at, orders relationship",
        "Order model: id (PK), user_id (FK to User), total_amount, status, items relationship",
        "OrderItem model: id (PK), order_id (FK to Order), product_name, quantity, unit_price",
        "Enforce cascade deletes or relationship back-references"
    ],
    required_artifacts=["models.py"],
    acceptance_criteria=[
        "models.py contains User, Order, OrderItem classes subclassing SQLAlchemy Base",
        "Foreign keys properly mapped between User -> Order -> OrderItem",
        "Passes schema instantiation and relationship traversal validation"
    ],
    timeout_seconds=25.0,
    initial_files={},
    validation_procedure="pytest",
    hidden_test_files={
        "test_hidden_db_models.py": """
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Order, OrderItem

def test_models_schema():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    user = User(email="test@example.com", username="tester")
    session.add(user)
    session.commit()

    order = Order(user_id=user.id, total_amount=150.0, status="PENDING")
    session.add(order)
    session.commit()

    item = OrderItem(order_id=order.id, product_name="Mechanical Keyboard", quantity=1, unit_price=150.0)
    session.add(item)
    session.commit()

    # Query back
    fetched_user = session.query(User).filter_by(email="test@example.com").first()
    assert fetched_user is not None
    assert len(fetched_user.orders) == 1
    assert fetched_user.orders[0].items[0].product_name == "Mechanical Keyboard"
"""
    }
)

TASK_05_FIX_BUG = BenchmarkTask(
    id="task_05_fix_bug",
    name="Fix Deliberate Off-by-One Bug in Cache",
    description="An LRU Cache implementation in 'lru_cache.py' has a subtle bug where capacity eviction occurs prematurely (capacity - 1 instead of capacity). Fix the bug so all tests pass.",
    category=TaskCategory.BUG_FIX,
    difficulty=TaskDifficulty.EASY,
    language="python",
    framework="pytest",
    template="bugfix-lru",
    requirements=[
        "Inspect 'lru_cache.py' and locate the premature eviction bug",
        "Ensure LRUCache maintains exactly 'capacity' items before evicting least recently used",
        "Preserve existing class methods get(key) and put(key, value)"
    ],
    required_artifacts=["lru_cache.py"],
    acceptance_criteria=[
        "LRUCache correctly stores up to capacity items",
        "Evicts oldest accessed item only when size strictly exceeds capacity",
        "All test cases pass"
    ],
    timeout_seconds=20.0,
    initial_files={
        "lru_cache.py": """
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = OrderedDict()

    def get(self, key: int) -> int:
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        # BUG HERE: evicts when size reaches capacity rather than exceeding capacity!
        if len(self.cache) >= self.capacity:
            self.cache.popitem(last=False)
"""
    },
    validation_procedure="pytest",
    hidden_test_files={
        "test_hidden_lru.py": """
import pytest
from lru_cache import LRUCache

def test_exact_capacity_retention():
    cache = LRUCache(2)
    cache.put(1, 10)
    cache.put(2, 20)
    # Both items must be present!
    assert cache.get(1) == 10
    assert cache.get(2) == 20

def test_eviction_on_overflow():
    cache = LRUCache(2)
    cache.put(1, 100)
    cache.put(2, 200)
    cache.put(3, 300) # Should evict 1
    assert cache.get(1) == -1
    assert cache.get(2) == 200
    assert cache.get(3) == 300

def test_update_existing_key():
    cache = LRUCache(2)
    cache.put(1, 10)
    cache.put(2, 20)
    cache.put(1, 99) # Update 1, does not evict 2
    assert cache.get(1) == 99
    assert cache.get(2) == 20
"""
    }
)

TASK_06_ADD_FEATURE = BenchmarkTask(
    id="task_06_add_feature",
    name="Add Feature Without Breaking Existing Tests",
    description="Extend the existing 'InventoryManager' in 'inventory.py' by adding a method 'filter_by_price_range(min_price, max_price)' without breaking any existing methods or tests.",
    category=TaskCategory.FEATURE_ADDITION,
    difficulty=TaskDifficulty.MEDIUM,
    language="python",
    framework="pytest",
    template="feature-addition",
    requirements=[
        "Add `filter_by_price_range(min_price: float, max_price: float) -> list` to InventoryManager in 'inventory.py'",
        "Return list of item dicts whose price satisfies min_price <= item.price <= max_price",
        "Keep existing methods (add_item, get_item, list_all) fully operational and intact"
    ],
    required_artifacts=["inventory.py"],
    acceptance_criteria=[
        "InventoryManager.filter_by_price_range implemented and returns correct items",
        "Existing add_item and list_all methods continue to work without regression",
        "All tests pass"
    ],
    timeout_seconds=20.0,
    initial_files={
        "inventory.py": """
class InventoryManager:
    def __init__(self):
        self.items = {}

    def add_item(self, item_id: str, name: str, price: float, quantity: int = 1):
        self.items[item_id] = {
            "id": item_id,
            "name": name,
            "price": price,
            "quantity": quantity
        }
        return self.items[item_id]

    def get_item(self, item_id: str):
        return self.items.get(item_id)

    def list_all(self):
        return list(self.items.values())
"""
    },
    validation_procedure="pytest",
    hidden_test_files={
        "test_hidden_inventory.py": """
import pytest
from inventory import InventoryManager

def test_existing_functionality_preserved():
    inv = InventoryManager()
    inv.add_item("item1", "Keyboard", 75.0, 5)
    inv.add_item("item2", "Mouse", 25.0, 10)
    assert inv.get_item("item1")["name"] == "Keyboard"
    assert len(inv.list_all()) == 2

def test_new_price_filter_feature():
    inv = InventoryManager()
    inv.add_item("a", "Budget Pen", 2.5)
    inv.add_item("b", "Desk Lamp", 35.0)
    inv.add_item("c", "Office Chair", 150.0)
    inv.add_item("d", "Monitor", 300.0)

    filtered = inv.filter_by_price_range(30.0, 200.0)
    names = [x["name"] for x in filtered]
    assert "Desk Lamp" in names
    assert "Office Chair" in names
    assert "Budget Pen" not in names
    assert "Monitor" not in names
"""
    }
)

TASK_07_REFACTOR_DUPLICATE = BenchmarkTask(
    id="task_07_refactor_duplicate",
    name="Refactor Duplicated Code",
    description="Refactor 'order_processor.py' to remove copy-pasted discount and tax calculation logic across retail and wholesale orders into reusable functions while preserving exact output behavior.",
    category=TaskCategory.REFACTORING,
    difficulty=TaskDifficulty.MEDIUM,
    language="python",
    framework="pytest",
    template="refactoring",
    requirements=[
        "Identify repetitive tax/discount calculation in 'order_processor.py'",
        "Extract common logic into helper functions `compute_discount` and `compute_tax`",
        "Keep `process_retail_order` and `process_wholesale_order` signatures and return formats unchanged"
    ],
    required_artifacts=["order_processor.py"],
    acceptance_criteria=[
        "Code is DRY and modular",
        "Exact calculations and return dictionary structure preserved",
        "All hidden unit tests pass"
    ],
    timeout_seconds=20.0,
    initial_files={
        "order_processor.py": """
def process_retail_order(subtotal: float, discount_pct: float, tax_rate: float) -> dict:
    # Duplicated calculation block
    discount_amount = round(subtotal * (discount_pct / 100.0), 2)
    taxable = subtotal - discount_amount
    tax_amount = round(taxable * (tax_rate / 100.0), 2)
    total = round(taxable + tax_amount, 2)
    return {
        "order_type": "retail",
        "subtotal": subtotal,
        "discount": discount_amount,
        "tax": tax_amount,
        "total": total
    }

def process_wholesale_order(subtotal: float, discount_pct: float, tax_rate: float) -> dict:
    # Identical duplicated calculation block
    discount_amount = round(subtotal * (discount_pct / 100.0), 2)
    taxable = subtotal - discount_amount
    tax_amount = round(taxable * (tax_rate / 100.0), 2)
    total = round(taxable + tax_amount, 2)
    return {
        "order_type": "wholesale",
        "subtotal": subtotal,
        "discount": discount_amount,
        "tax": tax_amount,
        "total": total
    }
"""
    },
    validation_procedure="pytest",
    hidden_test_files={
        "test_hidden_refactor.py": """
import pytest
from order_processor import process_retail_order, process_wholesale_order

def test_retail_order_exact_output():
    res = process_retail_order(100.0, 10.0, 8.0)
    assert res["discount"] == 10.0
    assert res["tax"] == 7.20
    assert res["total"] == 97.20
    assert res["order_type"] == "retail"

def test_wholesale_order_exact_output():
    res = process_wholesale_order(1000.0, 20.0, 5.0)
    assert res["discount"] == 200.0
    assert res["tax"] == 40.0
    assert res["total"] == 840.0
    assert res["order_type"] == "wholesale"
"""
    }
)

TASK_08_INPUT_VALIDATION = BenchmarkTask(
    id="task_08_input_validation",
    name="Implement Input Validation and Error Handling",
    description="Implement a strict registration validator in 'validator.py' that validates username (3-20 alphanum), email format, age (>= 18), and password complexity with clear error messages.",
    category=TaskCategory.VALIDATION,
    difficulty=TaskDifficulty.MEDIUM,
    language="python",
    framework="pytest",
    template="validation-suite",
    requirements=[
        "Implement `validate_registration_payload(data: dict) -> dict` in 'validator.py'",
        "Validate 'username': non-empty string, length 3 to 20 characters, alphanumeric only",
        "Validate 'email': contains '@' and valid domain with '.'",
        "Validate 'age': integer >= 18",
        "Validate 'password': at least 8 characters, contains at least one digit and one uppercase letter",
        "Return `{'is_valid': True, 'errors': []}` or `{'is_valid': False, 'errors': ['...']}`"
    ],
    required_artifacts=["validator.py"],
    acceptance_criteria=[
        "validator.py defines validate_registration_payload",
        "Detects all invalid cases and returns descriptive error list",
        "Passes hidden test cases"
    ],
    timeout_seconds=20.0,
    initial_files={},
    validation_procedure="pytest",
    hidden_test_files={
        "test_hidden_validator.py": """
import pytest
from validator import validate_registration_payload

def test_valid_payload():
    valid = {
        "username": "alex99",
        "email": "alex@example.com",
        "age": 25,
        "password": "SecurePassword1"
    }
    res = validate_registration_payload(valid)
    assert res["is_valid"] is True
    assert len(res["errors"]) == 0

def test_underage_and_bad_username():
    bad = {
        "username": "x!",
        "email": "alex@example.com",
        "age": 16,
        "password": "SecurePassword1"
    }
    res = validate_registration_payload(bad)
    assert res["is_valid"] is False
    assert len(res["errors"]) >= 2

def test_weak_password_and_invalid_email():
    bad = {
        "username": "coder",
        "email": "not-an-email",
        "age": 20,
        "password": "short"
    }
    res = validate_registration_payload(bad)
    assert res["is_valid"] is False
    errs = " ".join(res["errors"]).lower()
    assert "email" in errs
    assert "password" in errs
"""
    }
)

TASK_09_DOCUMENTATION = BenchmarkTask(
    id="task_09_generate_docs",
    name="Generate Documentation for Existing Project",
    description="Generate comprehensive markdown documentation in 'API_REFERENCE.md' detailing functions, parameters, return types, and usage examples for 'math_ops.py'.",
    category=TaskCategory.DOCUMENTATION,
    difficulty=TaskDifficulty.EASY,
    language="markdown",
    framework="markdown",
    template="documentation",
    requirements=[
        "Inspect 'math_ops.py' and its exported functions (vector_dot, matrix_multiply, cosine_similarity)",
        "Create 'API_REFERENCE.md' documenting each function's purpose, arguments, return type, and edge cases",
        "Include runnable code snippets in markdown code blocks",
        "Include an overview section and requirements section"
    ],
    required_artifacts=["API_REFERENCE.md"],
    acceptance_criteria=[
        "API_REFERENCE.md exists and is non-empty (> 300 characters)",
        "Mentions all three functions: vector_dot, matrix_multiply, cosine_similarity",
        "Contains valid markdown code blocks with python snippets"
    ],
    timeout_seconds=20.0,
    initial_files={
        "math_ops.py": """
import math
from typing import List

def vector_dot(a: List[float], b: List[float]) -> float:
    if len(a) != len(b):
        raise ValueError("Vectors must have identical length")
    return sum(x * y for x, y in zip(a, b))

def matrix_multiply(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    if not a or not b or len(a[0]) != len(b):
        raise ValueError("Matrix dimensions incompatible for multiplication")
    rows_a = len(a)
    cols_b = len(b[0])
    cols_a = len(a[0])
    result = [[0.0 for _ in range(cols_b)] for _ in range(rows_a)]
    for i in range(rows_a):
        for j in range(cols_b):
            result[i][j] = sum(a[i][k] * b[k][j] for k in range(cols_a))
    return result

def cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = vector_dot(a, b)
    norm_a = math.sqrt(vector_dot(a, a))
    norm_b = math.sqrt(vector_dot(b, b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
"""
    },
    validation_procedure="content_and_criteria",
    hidden_test_files={}
)

TASK_10_FIX_FAILING_TESTS = BenchmarkTask(
    id="task_10_fix_failing_tests",
    name="Fix Project with Intentionally Failing Tests",
    description="Fix the broken metrics aggregation service in 'metrics_calc.py' so that all existing unit tests in 'test_metrics.py' pass cleanly.",
    category=TaskCategory.BUG_FIX,
    difficulty=TaskDifficulty.MEDIUM,
    language="python",
    framework="pytest",
    template="failing-tests-repair",
    requirements=[
        "Diagnose why 'test_metrics.py' fails against 'metrics_calc.py'",
        "Fix ZeroDivisionError handling in calculate_average to return 0.0 for empty lists",
        "Fix percentile_95 calculation to sort values before indexing",
        "Make all tests in test_metrics.py pass without modifying test_metrics.py"
    ],
    required_artifacts=["metrics_calc.py"],
    acceptance_criteria=[
        "metrics_calc.py correctly handles empty arrays without crashing",
        "Percentile 95 calculation is accurate and sorted",
        "All unit tests in test_metrics.py pass"
    ],
    timeout_seconds=20.0,
    initial_files={
        "metrics_calc.py": """
from typing import List

def calculate_average(values: List[float]) -> float:
    # BUG: Crashes on empty list!
    return sum(values) / len(values)

def calculate_p95(values: List[float]) -> float:
    if not values:
        return 0.0
    # BUG: Fails to sort values before computing 95th percentile index!
    idx = int(0.95 * len(values))
    idx = min(idx, len(values) - 1)
    return values[idx]
""",
        "test_metrics.py": """
import pytest
from metrics_calc import calculate_average, calculate_p95

def test_average_normal():
    assert calculate_average([10.0, 20.0, 30.0]) == 20.0

def test_average_empty():
    assert calculate_average([]) == 0.0

def test_p95_unsorted_list():
    data = [100.0, 1.0, 50.0, 25.0, 75.0, 90.0, 10.0, 30.0, 40.0, 60.0]
    # P95 of this dataset must be close to highest values (e.g. >= 90)
    p95 = calculate_p95(data)
    assert p95 >= 90.0
"""
    },
    validation_procedure="pytest",
    hidden_test_files={
        "test_hidden_metrics.py": """
import pytest
from metrics_calc import calculate_average, calculate_p95

def test_all_metrics_edge_cases():
    assert calculate_average([]) == 0.0
    assert calculate_p95([]) == 0.0
    assert calculate_average([5.0]) == 5.0
    assert calculate_p95([5.0]) == 5.0
"""
    }
)


ALL_BENCHMARK_TASKS: List[BenchmarkTask] = [
    TASK_01_URL_PARSER,
    TASK_02_FASTAPI_CRUD,
    TASK_03_REACT_FRONTEND,
    TASK_04_DB_SCHEMA,
    TASK_05_FIX_BUG,
    TASK_06_ADD_FEATURE,
    TASK_07_REFACTOR_DUPLICATE,
    TASK_08_INPUT_VALIDATION,
    TASK_09_DOCUMENTATION,
    TASK_10_FIX_FAILING_TESTS,
]


def get_all_tasks() -> List[BenchmarkTask]:
    return list(ALL_BENCHMARK_TASKS)


def get_task_by_id(task_id: str) -> Optional[BenchmarkTask]:
    for t in ALL_BENCHMARK_TASKS:
        if t.id == task_id:
            return t
    return None
