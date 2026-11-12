"""
AIForge benchmark task set (v1, frozen).

Twenty fixed prompts covering the kinds of projects AIForge is meant to build.
Each task names the exact HTTP endpoints it requires, so the grader can check
*requirement coverage* objectively: it imports the generated FastAPI app inside
the sandbox and compares its real route table against ``expected_routes``.

Rules for editing this file
---------------------------
* Treat the set as frozen once you publish numbers. Changing a prompt changes
  the benchmark; bump ``TASKSET_VERSION`` and re-run every configuration.
* Keep prompts self-contained: no references to files the model cannot see.
* Paths use ``{param}`` for path parameters; the parameter name is ignored when
  matching, a trailing slash is ignored, everything else must match exactly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

TASKSET_VERSION = "v1"

Route = Tuple[str, str]  # (METHOD, "/path/{id}")


@dataclass(frozen=True)
class BenchmarkTask:
    id: str
    title: str
    category: str
    difficulty: str  # easy | medium | hard
    prompt: str
    expected_routes: List[Route] = field(default_factory=list)


def _spec(summary: str, routes: List[Route], extras: str = "") -> str:
    lines = "\n".join(f"- {m} {p}" for m, p in routes)
    tail = f"\n{extras}" if extras else ""
    return (
        f"{summary}\n\nUse Python with FastAPI. Expose exactly these HTTP endpoints:\n{lines}\n"
        "Include a pytest test suite that exercises the endpoints with FastAPI's TestClient."
        f"{tail}"
    )


_RAW: List[Tuple[str, str, str, str, str, List[Route], str]] = [
    # id, title, category, difficulty, summary, routes, extras
    ("todo-basic", "Todo list API", "crud", "easy",
     "Build a todo list REST API with an in-memory store.",
     [("GET", "/health"), ("GET", "/todos"), ("POST", "/todos"), ("GET", "/todos/{id}"),
      ("PUT", "/todos/{id}"), ("DELETE", "/todos/{id}")], ""),
    ("notes-sqlite", "Notes API with SQLite", "crud", "easy",
     "Build a notes REST API that persists notes in SQLite using SQLAlchemy.",
     [("GET", "/notes"), ("POST", "/notes"), ("GET", "/notes/{id}"), ("DELETE", "/notes/{id}")],
     "Notes have a title, body and created_at timestamp."),
    ("url-shortener", "URL shortener", "service", "easy",
     "Build a URL shortener service.",
     [("POST", "/shorten"), ("GET", "/{code}"), ("GET", "/stats/{code}")],
     "GET /{code} redirects with HTTP 307; /stats/{code} returns the click count."),
    ("calculator-api", "Calculator API", "service", "easy",
     "Build a calculator API with input validation.",
     [("POST", "/add"), ("POST", "/subtract"), ("POST", "/multiply"), ("POST", "/divide")],
     "Division by zero must return HTTP 400."),
    ("contact-book", "Contact book", "crud", "easy",
     "Build a contact book API with search by name.",
     [("GET", "/contacts"), ("POST", "/contacts"), ("GET", "/contacts/search"),
      ("PUT", "/contacts/{id}"), ("DELETE", "/contacts/{id}")],
     "GET /contacts/search takes a `q` query parameter."),
    ("auth-jwt", "REST API with JWT auth", "auth", "medium",
     "Build a REST API with user registration and JWT authentication. Passwords must be hashed.",
     [("POST", "/auth/register"), ("POST", "/auth/login"), ("GET", "/users/me")],
     "GET /users/me requires a Bearer token and returns 401 without one."),
    ("todo-auth", "Multi-user todo API", "auth", "medium",
     "Build a todo API where each user only sees their own todos, with JWT authentication.",
     [("POST", "/auth/register"), ("POST", "/auth/login"), ("GET", "/todos"), ("POST", "/todos"),
      ("DELETE", "/todos/{id}")],
     "Deleting another user's todo must return 404."),
    ("blog-api", "Blog with comments", "crud", "medium",
     "Build a blog API with posts and comments, stored in SQLite with SQLAlchemy.",
     [("GET", "/posts"), ("POST", "/posts"), ("GET", "/posts/{id}"), ("DELETE", "/posts/{id}"),
      ("GET", "/posts/{id}/comments"), ("POST", "/posts/{id}/comments")],
     "GET /posts supports `page` and `limit` query parameters."),
    ("expense-tracker", "Expense tracker", "crud", "medium",
     "Build an expense tracker API with categories and a monthly summary.",
     [("GET", "/expenses"), ("POST", "/expenses"), ("DELETE", "/expenses/{id}"),
      ("GET", "/expenses/summary")],
     "GET /expenses filters by an optional `category` query parameter; "
     "/expenses/summary takes `month` (YYYY-MM) and returns the total per category."),
    ("inventory-dashboard", "Inventory CRUD dashboard backend", "crud", "medium",
     "Build the backend for an inventory dashboard: products with stock levels and low-stock alerts.",
     [("GET", "/products"), ("POST", "/products"), ("PATCH", "/products/{id}"),
      ("DELETE", "/products/{id}"), ("GET", "/dashboard/low-stock"), ("GET", "/dashboard/stats")],
     "/dashboard/low-stock lists products whose stock is below their reorder_level."),
    ("library-system", "Library loans", "domain", "medium",
     "Build a library management API for books, members and loans.",
     [("GET", "/books"), ("POST", "/books"), ("POST", "/members"), ("POST", "/loans"),
      ("POST", "/loans/{id}/return"), ("GET", "/members/{id}/loans")],
     "A book that is already on loan cannot be loaned again (return HTTP 409)."),
    ("event-booking", "Event booking", "domain", "medium",
     "Build an event booking API with seat capacity limits.",
     [("GET", "/events"), ("POST", "/events"), ("POST", "/events/{id}/bookings"),
      ("GET", "/events/{id}/bookings"), ("DELETE", "/bookings/{id}")],
     "Booking a full event returns HTTP 409."),
    ("kanban-board", "Kanban board", "crud", "medium",
     "Build a kanban board API with boards, columns and cards that can be moved between columns.",
     [("POST", "/boards"), ("GET", "/boards/{id}"), ("POST", "/boards/{id}/columns"),
      ("POST", "/columns/{id}/cards"), ("PATCH", "/cards/{id}/move")], ""),
    ("quiz-app", "Quiz backend", "domain", "medium",
     "Build a quiz API: create quizzes with multiple-choice questions and score submissions.",
     [("POST", "/quizzes"), ("GET", "/quizzes/{id}"), ("POST", "/quizzes/{id}/submit")],
     "Submissions return the score and which answers were wrong. Never expose correct answers on GET."),
    ("rate-limited-api", "Rate-limited API", "service", "medium",
     "Build an API with a per-client rate limit of 5 requests per minute on GET /data.",
     [("GET", "/data"), ("GET", "/health")],
     "The 6th request within a minute from the same client returns HTTP 429."),
    ("ecommerce-cart", "E-commerce cart & orders", "domain", "hard",
     "Build an e-commerce backend with a product catalog, shopping cart and order checkout, "
     "with JWT authentication for customers.",
     [("POST", "/auth/register"), ("POST", "/auth/login"), ("GET", "/products"),
      ("POST", "/cart/items"), ("GET", "/cart"), ("DELETE", "/cart/items/{id}"),
      ("POST", "/orders"), ("GET", "/orders")],
     "Checkout computes the order total server-side and empties the cart."),
    ("bank-ledger", "Bank ledger", "domain", "hard",
     "Build a bank account ledger API with deposits, withdrawals and transfers.",
     [("POST", "/accounts"), ("GET", "/accounts/{id}"), ("POST", "/accounts/{id}/deposit"),
      ("POST", "/accounts/{id}/withdraw"), ("POST", "/transfers"),
      ("GET", "/accounts/{id}/transactions")],
     "Withdrawals and transfers that would overdraw an account return HTTP 400. "
     "Use Decimal, not float, for money."),
    ("rbac-admin", "Role-based admin API", "auth", "hard",
     "Build an API with JWT auth and two roles, admin and user. Only admins can manage users.",
     [("POST", "/auth/login"), ("GET", "/admin/users"), ("POST", "/admin/users"),
      ("DELETE", "/admin/users/{id}"), ("GET", "/me")],
     "A normal user calling /admin/* gets HTTP 403."),
    ("chat-rooms", "Chat rooms with history", "service", "hard",
     "Build a chat API with rooms, message history and a WebSocket endpoint for live messages.",
     [("POST", "/rooms"), ("GET", "/rooms"), ("GET", "/rooms/{id}/messages"),
      ("POST", "/rooms/{id}/messages")],
     "Also expose a WebSocket at /ws/{room_id} that broadcasts new messages."),
    ("job-queue", "Background job queue", "service", "hard",
     "Build an API that accepts jobs, processes them in the background and reports status.",
     [("POST", "/jobs"), ("GET", "/jobs/{id}"), ("GET", "/jobs"), ("POST", "/jobs/{id}/cancel")],
     "Job status moves through queued -> running -> done | failed | cancelled."),
]


TASKS: List[BenchmarkTask] = [
    BenchmarkTask(id=i, title=t, category=c, difficulty=d, prompt=_spec(s, r, e), expected_routes=r)
    for (i, t, c, d, s, r, e) in _RAW
]


def get_tasks(ids: List[str] | None = None) -> List[BenchmarkTask]:
    if not ids:
        return list(TASKS)
    by_id = {t.id: t for t in TASKS}
    unknown = [i for i in ids if i not in by_id]
    if unknown:
        raise KeyError(f"Unknown task id(s): {unknown}. Known: {sorted(by_id)}")
    return [by_id[i] for i in ids]
