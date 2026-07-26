import pytest
from fastapi.testclient import TestClient

from backend.learning.extractor import LearningExtractor
from backend.learning.knowledge_base import KnowledgeBase
from backend.learning.embeddings import LearningEmbeddings
from backend.learning.retriever import KnowledgeRetriever
from backend.learning.scorer import KnowledgeScorer
from backend.learning.versioning import KnowledgeVersioning
from backend.learning.analytics import LearningAnalytics
from backend.main import app

client = TestClient(app)


def test_learning_extractor():
    """Test 1: LearningExtractor pattern extraction from completed projects."""
    extractor = LearningExtractor()

    files = {
        "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()\n# jwt auth middleware",
        "frontend/src/App.jsx": "import React from 'react'; export default function App() {}"
    }

    res = extractor.extract_knowledge("Clinic Management", files)
    assert res["extracted_count"] >= 2
    assert any(p["category"] == "Backend APIs" for p in res["patterns"])


def test_knowledge_base_operations():
    """Test 2: KnowledgeBase storing, listing, and architecture templates."""
    kb = KnowledgeBase()

    entry = kb.store_pattern("GraphQL API Pattern", "Backend APIs", "Async Strawberry GraphQL Integration", ["graphql"])
    assert entry["id"].startswith("kb_")

    all_entries = kb.list_knowledge()
    assert len(all_entries) >= 4

    templates = kb.get_templates()
    assert "e_commerce" in templates
    assert "hospital_management" in templates


def test_semantic_embeddings_and_retriever():
    """Test 3: LearningEmbeddings generation and KnowledgeRetriever semantic search."""
    retriever = KnowledgeRetriever()

    results = retriever.search_knowledge("JWT Authentication OAuth2", top_k=3)
    assert len(results) >= 1
    assert "knowledge_item" in results[0]
    assert results[0]["similarity_score"] > -1.0


def test_knowledge_scorer_and_versioning():
    """Test 4: KnowledgeScorer confidence calculation and KnowledgeVersioning."""
    scorer = KnowledgeScorer()
    versioning = KnowledgeVersioning()

    conf = scorer.calculate_confidence(reuse_count=20, success_rate=0.99)
    assert conf >= 9.5

    v_next = versioning.bump_version("1.0")
    assert v_next == "1.1"


def test_learning_analytics():
    """Test 5: LearningAnalytics telemetry metrics calculation."""
    analytics = LearningAnalytics()

    data = analytics.get_analytics()
    assert data["projects_learned"] >= 20
    assert data["total_knowledge_entries"] >= 3
    assert data["average_confidence_score"] > 8.0


def test_learning_api_endpoints():
    """Test 6: FastAPI Learning endpoints (/api/knowledge, /api/knowledge/search, /api/knowledge/store, /api/knowledge/templates, /api/learning/analytics)."""
    # 1. GET /api/knowledge
    res_list = client.get("/api/knowledge")
    assert res_list.status_code == 200
    assert "entries" in res_list.json()

    # 2. GET /api/knowledge/search
    res_search = client.get("/api/knowledge/search?q=Authentication")
    assert res_search.status_code == 200
    assert "results" in res_search.json()

    # 3. POST /api/knowledge/store
    res_store = client.post("/api/knowledge/store", json={
        "name": "Redis Caching Layer",
        "category": "Optimization",
        "description": "FastAPI async Redis cache decorator",
        "tags": ["redis", "cache"]
    })
    assert res_store.status_code == 200
    assert res_store.json()["status"] == "success"

    # 4. GET /api/knowledge/templates
    res_tpl = client.get("/api/knowledge/templates")
    assert res_tpl.status_code == 200
    assert "templates" in res_tpl.json()

    # 5. GET /api/learning/analytics
    res_ana = client.get("/api/learning/analytics")
    assert res_ana.status_code == 200
    assert res_ana.json()["projects_learned"] >= 20
