"""
AIForge Day 96 & 97 Knowledge Base & Reusable Component Library
===============================================================
Maintains reusable knowledge templates & best practices for:
- React Authentication
- JWT Bearer Middleware
- CRUD APIs
- Docker Containerization
- Redis Caching
- FastAPI Architecture
- Testing Strategy
- CI/CD Workflows
- OAuth Integration
- Payment Gateway (Stripe/PayPal)
- Charts & Visualization
- Admin Dashboard
"""

import json
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.learning.knowledge_base")


class ReusableKnowledgeBase:
    """
    Knowledge Base for reusable software components and best practices.
    """

    def __init__(self) -> None:
        self.catalog = {
            "React Authentication": {
                "category": "frontend",
                "description": "Stateless JWT Auth Provider with Context API and localStorage token persistence",
                "best_practices": ["Store JWT in secure HTTPOnly cookie or encrypted memory", "Auto refresh token on 401"],
                "reusable_template": "export const AuthProvider = ({ children }) => { ... }",
                "common_bugs": ["Token expiration unhandled causing UI crash"],
                "solutions": ["Add axios request/response interceptors for silent refresh"]
            },
            "JWT": {
                "category": "security",
                "description": "HS256 or RS256 JWT validation middleware for FastAPI routes",
                "best_practices": ["Use short-lived access tokens (15m) and refresh tokens (7d)"],
                "reusable_template": "def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)): ...",
                "common_bugs": ["Algorithm mismatch or missing secret key"],
                "solutions": ["Enforce ALGORITHM='HS256' in PyJWT decode"]
            },
            "CRUD APIs": {
                "category": "backend",
                "description": "Standardized RESTful CRUD route patterns with Pydantic validation",
                "best_practices": ["Use HTTP 201 for Created, 204 for No Content", "Paginate GET list endpoints"],
                "reusable_template": "@router.get('/items', response_model=List[ItemSchema]) ...",
                "common_bugs": ["N+1 query loading in database relationships"],
                "solutions": ["Use joinedload or selectinload in SQLAlchemy queries"]
            },
            "Docker": {
                "category": "devops",
                "description": "Multi-stage production Dockerfile and Docker Compose orchestration",
                "best_practices": ["Use alpine base images", "Run container as non-root user"],
                "reusable_template": "FROM node:18-alpine AS builder ...",
                "common_bugs": ["Oversized container build context"],
                "solutions": ["Add .dockerignore ignoring node_modules and build artifacts"]
            },
            "Redis": {
                "category": "database",
                "description": "In-memory caching and rate-limiting store",
                "best_practices": ["Set TTL expiration on cached keys", "Use Redis connection pool"],
                "reusable_template": "redis_client = redis.Redis(host='localhost', port=6379, db=0)",
                "common_bugs": ["Unbounded cache growth filling memory"],
                "solutions": ["Configure maxmemory-policy volatile-lru"]
            },
            "FastAPI": {
                "category": "backend",
                "description": "Asynchronous RESTful API framework with Swagger OpenAPI documentation",
                "best_practices": ["Group routes into APIRouters", "Use dependency injection for DB sessions"],
                "reusable_template": "app = FastAPI(title='AIForge Microservice')",
                "common_bugs": ["Blocking sync IO calls inside async path functions"],
                "solutions": ["Use async def with async libraries or run_in_executor for sync IO"]
            },
            "Testing": {
                "category": "qa",
                "description": "Pytest unit & integration test suite with coverage reports",
                "best_practices": ["Mock external network calls", "Use test fixtures for DB setup"],
                "reusable_template": "def test_api_endpoint(client): response = client.get('/health'); assert response.status_code == 200",
                "common_bugs": ["Test pollution across test runs"],
                "solutions": ["Rollback database transaction after each test case"]
            },
            "CI/CD": {
                "category": "devops",
                "description": "GitHub Actions automated build, test, and cloud deployment workflow",
                "best_practices": ["Run linter and tests before merge", "Use repository secrets for keys"],
                "reusable_template": "name: CI/CD Pipeline\non: [push]",
                "common_bugs": ["Failing build due to un-pinned dependencies"],
                "solutions": ["Use package-lock.json / poetry.lock / requirements.txt with exact versions"]
            },
            "OAuth": {
                "category": "security",
                "description": "Google & GitHub OAuth2 Social Authentication Flow",
                "best_practices": ["Validate state parameter to prevent CSRF"],
                "reusable_template": "async def oauth_callback(code: str): ...",
                "common_bugs": ["Mismatched redirect URI"],
                "solutions": ["Match exact redirect URI in OAuth app console"]
            },
            "Payment Gateway": {
                "category": "integration",
                "description": "Stripe Payment Intent and Webhook Event Processor",
                "best_practices": ["Verify Stripe webhook signature"],
                "reusable_template": "stripe.PaymentIntent.create(amount=total, currency='usd')",
                "common_bugs": ["Duplicate event processing from retried webhooks"],
                "solutions": ["Store processed webhook event IDs in database for idempotency"]
            },
            "Charts": {
                "category": "frontend",
                "description": "Recharts / Chart.js Data Analytics Visualization Component",
                "best_practices": ["Memoize chart dataset calculation"],
                "reusable_template": "<ResponsiveContainer><LineChart data={data}><Line dataKey='val'/></LineChart></ResponsiveContainer>",
                "common_bugs": ["Re-rendering entire chart canvas on every state tick"],
                "solutions": ["Wrap chart component in React.memo"]
            },
            "Admin Dashboard": {
                "category": "frontend",
                "description": "Role-Based Admin Portal with Data Tables, Metrics Cards, and User Management",
                "best_practices": ["Protect admin routes with Role-Based Access Control (RBAC)"],
                "reusable_template": "export function AdminDashboard() { ... }",
                "common_bugs": ["Exposing admin APIs without RBAC authorization check"],
                "solutions": ["Add require_admin role check dependency in FastAPI router"]
            }
        }

    def get_all_knowledge(self) -> Dict[str, Any]:
        return {
            "total_components": len(self.catalog),
            "catalog": self.catalog
        }

    def get_component(self, name: str) -> Optional[Dict[str, Any]]:
        return self.catalog.get(name)


global_knowledge_base = ReusableKnowledgeBase()
