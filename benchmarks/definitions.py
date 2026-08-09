"""
AIForge Real Application Benchmark Suite Definitions (Phase 12)
===============================================================
5 Real-world software application specifications for evaluating AIForge E2E autonomous pipeline.
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


class BenchmarkSpec(BaseModel):
    name: str = Field(..., description="Benchmark application name")
    description: str = Field(..., description="Detailed natural language application specification")
    technology_stack: str = Field(default="FastAPI, Python, PostgreSQL, React, Pytest", description="Required technology stack")
    requirements: List[str] = Field(default_factory=list, description="Explicit deterministic requirement list")


BENCHMARK_SUITE: List[BenchmarkSpec] = [
    BenchmarkSpec(
        name="TodoApp",
        description="Build a Todo application with user authentication, CRUD operations for tasks, mark complete functionality, PostgreSQL database persistence, FastAPI REST API, and Pytest integration tests.",
        requirements=[
            "User registration and JWT login authentication endpoints",
            "POST /api/todos to create a new task with title and priority",
            "GET /api/todos to list user tasks",
            "PUT /api/todos/{id} to update or mark task completed",
            "DELETE /api/todos/{id} to remove a task",
            "PostgreSQL database schema with foreign keys",
            "Pytest test suite covering authentication and todo endpoints"
        ]
    ),
    BenchmarkSpec(
        name="BlogAPI",
        description="Build a Blog API service with user authentication, CRUD post management, article comments, database persistence, pagination, REST API, and Pytest integration tests.",
        requirements=[
            "User authentication and author roles",
            "POST /api/posts to publish article posts",
            "GET /api/posts with page and limit pagination query parameters",
            "POST /api/posts/{id}/comments to add comments to articles",
            "DELETE /api/posts/{id} to delete posts by author",
            "Normalized relational schema for users, posts, and comments",
            "Pytest suite verifying pagination and post CRUD logic"
        ]
    ),
    BenchmarkSpec(
        name="ExpenseTracker",
        description="Build an Expense Tracker application with user authentication, income and expense records, category tagging, monthly summary reporting, database persistence, REST API, and Pytest integration tests.",
        requirements=[
            "User registration and login auth",
            "POST /api/expenses to log income or expense transactions",
            "GET /api/expenses to list transactions filtered by category",
            "GET /api/expenses/summary to return monthly totals and net balance",
            "Categories table and transaction foreign key relations",
            "Pytest integration suite testing monthly calculations and category filters"
        ]
    ),
    BenchmarkSpec(
        name="AuthDashboard",
        description="Build an Auth Dashboard service with user registration, login, JWT token authentication, protected API routes, user profile updates, dashboard metrics endpoint, and Pytest integration tests.",
        requirements=[
            "POST /api/auth/register and POST /api/auth/login",
            "Bearer JWT token authorization header validation middleware",
            "GET /api/user/profile to view user profile details",
            "PUT /api/user/profile to update user details",
            "GET /api/dashboard/stats to return system usage statistics for authenticated users",
            "Pytest suite verifying unauthorized HTTP 401 responses and token lifecycle"
        ]
    ),
    BenchmarkSpec(
        name="ECommerce",
        description="Build an E-Commerce backend service with product catalog, category filtering, user authentication, shopping cart management, order creation, database persistence, REST API, and Pytest integration tests.",
        requirements=[
            "GET /api/products and GET /api/products/{id}",
            "User authentication for customer accounts",
            "POST /api/cart/items to add items to shopping cart",
            "POST /api/orders to place an order from active cart items",
            "GET /api/orders to list customer past orders",
            "Normalized schema for products, cart, orders, and order items",
            "Pytest suite verifying cart total calculation and checkout order creation"
        ]
    )
]
