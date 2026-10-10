"""
AIForge Automated Test Suite — Persistent Project Memory & Codebase Intelligence
================================================================================
Comprehensive verification of:
1. 3-Tier Project Memory (Project, Codebase, Execution) with Project Isolation
2. Memory Conflict Resolution & Superseding (ACTIVE vs SUPERSEDED)
3. Language-Aware Codebase Indexing & Symbol Extraction (Python, React/JS, SQL)
4. Incremental Indexing with SHA256 File Hashing & Unchanged File Skipping
5. Secret & Sensitive File Sanitization and Exclusion (.env, *.key, secrets)
6. Lightweight Code Dependency Graph Engine
7. Transitive Change Impact Analysis (Affected Files, Routes, Models, Tests)
8. Task-Tailored Agent Context Builder (Planner, Architect, Frontend, Backend, Database, Debug)
9. Multi-Session Project Modification Lineage & Versioning (v1 -> v2)
10. FastAPI REST Endpoints Integration
"""

import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.database.models import (
    ProjectMemoryItemModel,
    CodebaseFileIndexModel,
    CodeDependencyModel,
    ProjectVersionSnapshotModel
)
from backend.memory.project_memory_service import ProjectMemoryService, sanitize_memory_content
from backend.memory.codebase_indexer import CodebaseIndexer, is_secret_or_excluded_file, compute_file_hash
from backend.memory.dependency_graph import CodeDependencyGraph
from backend.memory.impact_analyzer import ChangeImpactAnalyzer
from backend.services.context_builder import AgentContextBuilder
from backend.quality.version_manager import VersionManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_memory_service(tmp_path):
    store_file = tmp_path / "test_memory_records.json"
    return ProjectMemoryService(store_path=str(store_file))


@pytest.fixture
def tmp_codebase_indexer(tmp_path):
    store_file = tmp_path / "test_codebase_index.json"
    return CodebaseIndexer(store_path=str(store_file))


@pytest.fixture
def tmp_dep_graph(tmp_path):
    store_file = tmp_path / "test_dep_graphs.json"
    return CodeDependencyGraph(store_path=str(store_file))


@pytest.fixture
def sample_ecommerce_files():
    return {
        "backend/main.py": (
            "from fastapi import FastAPI\n"
            "from backend.routes.products import router as products_router\n"
            "app = FastAPI()\n"
            "app.include_router(products_router)\n"
        ),
        "backend/models/product.py": (
            "class Product:\n"
            "    id: int\n"
            "    name: str\n"
            "    price: float\n"
        ),
        "backend/routes/products.py": (
            "from fastapi import APIRouter\n"
            "from backend.models.product import Product\n"
            "router = APIRouter()\n"
            "@router.get('/api/products')\n"
            "def get_products():\n"
            "    return []\n"
            "@router.post('/api/products')\n"
            "def create_product(prod: Product):\n"
            "    return prod\n"
        ),
        "frontend/src/services/productApi.js": (
            "import axios from 'axios';\n"
            "export const fetchProducts = () => axios.get('/api/products');\n"
        ),
        "frontend/src/components/ProductList.jsx": (
            "import React from 'react';\n"
            "import { fetchProducts } from '../services/productApi';\n"
            "export const ProductList = () => {\n"
            "    return <div>Product List</div>;\n"
            "};\n"
        ),
        "tests/test_products.py": (
            "from backend.routes.products import get_products\n"
            "def test_get_products():\n"
            "    assert get_products() == []\n"
        ),
        "schema.sql": (
            "CREATE TABLE IF NOT EXISTS products (\n"
            "    id SERIAL PRIMARY KEY,\n"
            "    name VARCHAR(255) NOT NULL,\n"
            "    price NUMERIC(10, 2)\n"
            ");\n"
        ),
    }


# ---------------------------------------------------------------------------
# 1. Project Memory & Multi-Tenant Isolation Tests
# ---------------------------------------------------------------------------

def test_project_memory_crud_and_isolation(tmp_memory_service):
    # Store memory for Project A
    mem_a = tmp_memory_service.save_project_memory(
        project_id="proj_ecommerce_a",
        memory_type="ARCHITECTURE",
        key="backend_framework",
        value="FastAPI",
        importance="CRITICAL"
    )
    assert mem_a["id"] is not None
    assert mem_a["key"] == "backend_framework"
    assert mem_a["status"] == "ACTIVE"

    # Store memory for Project B
    mem_b = tmp_memory_service.save_project_memory(
        project_id="proj_fintech_b",
        memory_type="ARCHITECTURE",
        key="backend_framework",
        value="Django",
        importance="HIGH"
    )

    # Verify Project Isolation
    proj_a_mems = tmp_memory_service.get_active_memories("proj_ecommerce_a")
    proj_b_mems = tmp_memory_service.get_active_memories("proj_fintech_b")

    assert len(proj_a_mems) == 1
    assert proj_a_mems[0]["value"] == "FastAPI"

    assert len(proj_b_mems) == 1
    assert proj_b_mems[0]["value"] == "Django"

    # Test Delete
    assert tmp_memory_service.delete_project_memory("proj_ecommerce_a", mem_a["id"]) is True
    assert len(tmp_memory_service.get_active_memories("proj_ecommerce_a")) == 0
    # Project B remains intact
    assert len(tmp_memory_service.get_active_memories("proj_fintech_b")) == 1


def test_memory_conflict_resolution_and_superseding(tmp_memory_service):
    # Decision 1: Use MongoDB
    old_dec = tmp_memory_service.save_project_memory(
        project_id="proj_alpha",
        memory_type="DATABASE",
        key="database_choice",
        value="MongoDB",
        importance="HIGH"
    )

    # Decision 2: Switch to PostgreSQL superseding the old decision
    new_dec = tmp_memory_service.save_project_memory(
        project_id="proj_alpha",
        memory_type="DATABASE",
        key="database_choice",
        value="PostgreSQL 16",
        importance="CRITICAL",
        supersedes_key="database_choice"
    )

    # Active memories must ONLY return the new decision
    active_mems = tmp_memory_service.get_active_memories("proj_alpha")
    assert len(active_mems) == 1
    assert active_mems[0]["value"] == "PostgreSQL 16"
    assert active_mems[0]["status"] == "ACTIVE"

    # History retrieval includes the superseded record
    all_history = tmp_memory_service.get_all_memories("proj_alpha", include_superseded=True)
    assert len(all_history) == 2

    superseded_item = [m for m in all_history if m["id"] == old_dec["id"]][0]
    assert superseded_item["status"] == "SUPERSEDED"
    assert superseded_item["superseded_by"] == new_dec["id"]


# ---------------------------------------------------------------------------
# 2. Secret Sanitization & Exclusion Tests
# ---------------------------------------------------------------------------

def test_secret_exclusion_and_sanitization():
    # File path exclusion
    assert is_secret_or_excluded_file(".env") is True
    assert is_secret_or_excluded_file(".env.production") is True
    assert is_secret_or_excluded_file("credentials.json") is True
    assert is_secret_or_excluded_file("secrets/private.key") is True
    assert is_secret_or_excluded_file("certs/server.pem") is True
    assert is_secret_or_excluded_file("node_modules/axios/index.js") is True

    # Normal code files must not be excluded
    assert is_secret_or_excluded_file("backend/main.py") is False
    assert is_secret_or_excluded_file("frontend/src/App.jsx") is False

    # Text content sanitization
    dirty_text = "Database URL: postgresql://admin:secret123@localhost:5432/db with api_key='sk-live-99999999999999999999'"
    clean_text = sanitize_memory_content(dirty_text)
    assert "secret123" not in clean_text
    assert "sk-live" not in clean_text
    assert "[REDACTED_DATABASE_URL]" in clean_text or "[REDACTED_SECRET]" in clean_text


# ---------------------------------------------------------------------------
# 3. Codebase Intelligence & Incremental Indexing Tests
# ---------------------------------------------------------------------------

def test_codebase_symbol_extraction(tmp_codebase_indexer, sample_ecommerce_files):
    metrics = tmp_codebase_indexer.index_project_files("proj_ecom", sample_ecommerce_files)
    assert metrics["indexed_count"] == len(sample_ecommerce_files)
    assert metrics["skipped_count"] == 0

    idx = tmp_codebase_indexer.get_project_index("proj_ecom")

    # Verify Python route and model extraction
    route_file = idx["backend/routes/products.py"]
    assert "python" in route_file["language"]
    assert "get_products" in route_file["symbols"]
    assert any(r["path"] == "/api/products" for r in route_file["routes"])

    # Verify React component extraction
    comp_file = idx["frontend/src/components/ProductList.jsx"]
    assert "ProductList" in comp_file["components"]

    # Verify SQL table extraction
    sql_file = idx["schema.sql"]
    assert "products" in sql_file["models"]


def test_incremental_indexing_skips_unchanged_files(tmp_codebase_indexer, sample_ecommerce_files):
    # Initial Indexing
    run1 = tmp_codebase_indexer.index_project_files("proj_ecom", sample_ecommerce_files)
    assert run1["indexed_count"] == len(sample_ecommerce_files)
    assert run1["skipped_count"] == 0

    # Second Indexing without changes (Must skip all files)
    run2 = tmp_codebase_indexer.index_project_files("proj_ecom", sample_ecommerce_files)
    assert run2["indexed_count"] == 0
    assert run2["skipped_count"] == len(sample_ecommerce_files)

    # Modify 1 file and add 1 new file
    modified_files = dict(sample_ecommerce_files)
    modified_files["backend/routes/products.py"] += "\n@router.get('/api/products/search')\ndef search_products(): pass\n"
    modified_files["backend/routes/wishlist.py"] = "@router.get('/api/wishlist')\ndef get_wishlist(): pass\n"

    run3 = tmp_codebase_indexer.index_project_files("proj_ecom", modified_files)
    assert run3["indexed_count"] == 2  # 1 modified + 1 new
    assert run3["skipped_count"] == len(sample_ecommerce_files) - 1


# ---------------------------------------------------------------------------
# 4. Dependency Graph & Change Impact Analysis Tests
# ---------------------------------------------------------------------------

def test_dependency_graph_and_impact_analysis(tmp_codebase_indexer, tmp_dep_graph, sample_ecommerce_files):
    tmp_codebase_indexer.index_project_files("proj_ecom", sample_ecommerce_files)
    proj_idx = tmp_codebase_indexer.get_project_index("proj_ecom")

    graph = tmp_dep_graph.build_graph_from_index("proj_ecom", proj_idx)
    assert graph["node_count"] == len(sample_ecommerce_files)
    assert graph["edge_count"] > 0

    # Analyze change impact when modifying backend/models/product.py
    analyzer = ChangeImpactAnalyzer(indexer=tmp_codebase_indexer, dep_graph=tmp_dep_graph)
    report = analyzer.analyze_change_impact("proj_ecom", targets=["backend/models/product.py"])

    assert "backend/models/product.py" in report.affected_files
    assert any("routes/products.py" in f for f in report.affected_files)
    assert any("test_products.py" in f for f in report.affected_tests)
    assert report.impact_level in ("MEDIUM", "HIGH", "CRITICAL")
    assert "Impact Analysis" in report.summary


# ---------------------------------------------------------------------------
# 5. Task-Tailored Context Builder Tests
# ---------------------------------------------------------------------------

def test_centralized_context_builder(tmp_memory_service, tmp_codebase_indexer, sample_ecommerce_files):
    # Setup memories
    tmp_memory_service.save_project_memory(
        project_id="proj_ecom",
        memory_type="ARCHITECTURE",
        key="backend_framework",
        value="FastAPI + SQLAlchemy",
        importance="CRITICAL"
    )
    tmp_codebase_indexer.index_project_files("proj_ecom", sample_ecommerce_files)

    builder = AgentContextBuilder(memory_service=tmp_memory_service, indexer=tmp_codebase_indexer)

    # Planner Context
    planner_ctx = builder.build_agent_context(
        project_id="proj_ecom",
        agent_name="planner",
        prompt="Add wishlist functionality"
    )
    assert "Planner Goal" in planner_ctx
    assert "FastAPI" in planner_ctx

    # Backend Agent Context
    backend_ctx = builder.build_agent_context(
        project_id="proj_ecom",
        agent_name="backend",
        prompt="Add wishlist endpoint"
    )
    assert "Target Architecture" in backend_ctx

    # Debug Agent Context with past failure hints
    debug_ctx = builder.build_agent_context(
        project_id="proj_ecom",
        agent_name="debug",
        prompt="Fix import error in test",
        state={"test_results": {"failure_category": "IMPORT_ERROR", "failed_tests": ["test_wishlist"]}}
    )
    assert "Failure Diagnostics" in debug_ctx
    assert "IMPORT_ERROR" in debug_ctx


# ---------------------------------------------------------------------------
# 6. Multi-Session Project Modification Lineage (v1 -> v2)
# ---------------------------------------------------------------------------

def test_multi_session_project_versioning():
    v_manager = VersionManager()

    # Session 1: Create Core E-Commerce (v1)
    v1 = v_manager.create_snapshot(
        project_id="proj_demo_ecom",
        files_map={"backend/main.py": "app = FastAPI()", "frontend/App.jsx": "export default App;"},
        repair_reason="Initial Build",
        quality_score=95.0
    )
    assert v1.version_id == "v1"
    assert len(v_manager.get_history("proj_demo_ecom")) == 1

    # Session 2: User requests "Add Wishlist" (v2)
    v2_files = {
        "backend/main.py": "app = FastAPI()\n# with wishlist",
        "backend/routes/wishlist.py": "router = APIRouter()",
        "frontend/App.jsx": "export default App;",
        "frontend/components/Wishlist.jsx": "export const Wishlist = () => {};"
    }
    v2 = v_manager.create_snapshot(
        project_id="proj_demo_ecom",
        files_map=v2_files,
        repair_reason="Add wishlist functionality",
        changed_files=["backend/main.py", "backend/routes/wishlist.py", "frontend/components/Wishlist.jsx"],
        quality_score=98.0
    )
    assert v2.version_id == "v2"
    assert v2.parent_version == "v1"
    assert len(v_manager.get_history("proj_demo_ecom")) == 2

    # Latest version check
    latest = v_manager.get_latest_version("proj_demo_ecom")
    assert latest.version_id == "v2"
    assert "backend/routes/wishlist.py" in latest.files_snapshot


# ---------------------------------------------------------------------------
# 7. FastAPI REST API Endpoints Integration Tests
# ---------------------------------------------------------------------------

def test_project_memory_rest_api():
    client = TestClient(app)

    # 1. Store memory via REST API
    res = client.post("/api/projects/proj_api_test/memory", json={
        "memory_type": "ARCHITECTURE",
        "key": "database_persistence",
        "value": "PostgreSQL 16",
        "importance": "CRITICAL"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    mem_id = data["memory"]["id"]

    # 2. Retrieve memories
    res_get = client.get("/api/projects/proj_api_test/memory")
    assert res_get.status_code == 200
    memories = res_get.json()
    assert len(memories) >= 1
    assert any(m["key"] == "database_persistence" for m in memories)

    # 3. Analyze Change Impact via REST API
    res_impact = client.post("/api/projects/proj_api_test/codebase/impact", json={
        "targets": ["database_persistence"],
        "prompt": "Switch database to MongoDB"
    })
    assert res_impact.status_code == 200
    impact_data = res_impact.json()
    assert "affected_files" in impact_data
    assert "impact_level" in impact_data

    # 4. Delete memory
    res_del = client.delete(f"/api/projects/proj_api_test/memory/{mem_id}")
    assert res_del.status_code == 200
    assert res_del.json()["status"] == "SUCCESS"
