import pytest
from fastapi.testclient import TestClient

from backend.quality.analyzer import CodeAnalyzer
from backend.quality.security import SecurityScanner
from backend.quality.optimizer import PerformanceOptimizer
from backend.quality.duplicate_detector import DuplicateDetector
from backend.quality.metrics import QualityScoreCalculator
from backend.quality.report_generator import QualityReportGenerator
from backend.main import app

client = TestClient(app)


def test_static_code_analyzer():
    """Test 1: Static AST code analysis and complexity calculation."""
    analyzer = CodeAnalyzer()

    py_code = (
        "def compute(x):\n"
        "    if x > 10:\n"
        "        for i in range(x):\n"
        "            if i % 2 == 0:\n"
        "                print(i)\n"
    )

    res_py = analyzer.analyze_python("backend/services/calc.py", py_code)
    assert res_py["is_valid"] is True
    assert res_py["complexity"] >= 3

    jsx_code = "export default function Component() { return <div>Hello</div>; }"
    res_jsx = analyzer.analyze_react("frontend/src/Component.jsx", jsx_code)
    assert res_jsx["is_valid"] is True


def test_security_scanner_vulnerabilities():
    """Test 2: SecurityScanner hardcoded secret and SQL injection risk detection."""
    scanner = SecurityScanner()

    insecure_files = {
        "config.py": "JWT_SECRET = 'my_super_secret_key_12345'",
        "query.py": "query = 'SELECT * FROM users WHERE username=' + user_input"
    }

    res = scanner.scan_files(insecure_files)
    assert res["total_vulnerabilities"] >= 1
    assert any(v["type"] in ("HardcodedSecret", "SQLInjectionRisk") for v in res["vulnerabilities"])


def test_performance_optimizer_recommendations():
    """Test 3: PerformanceOptimizer database index & async route handler analysis."""
    optimizer = PerformanceOptimizer()

    files = {
        "schema.sql": "CREATE TABLE orders (id SERIAL PRIMARY KEY, user_id INT, FOREIGN KEY (user_id) REFERENCES users(id));",
        "main.py": "def get_orders(): pass"
    }

    res = optimizer.analyze_performance(files)
    assert res["total_recommendations"] >= 1
    assert any("Index" in r["issue"] or "Synchronous" in r["issue"] for r in res["recommendations"])


def test_duplicate_detector():
    """Test 4: DuplicateDetector code chunk duplication analysis."""
    detector = DuplicateDetector()

    repeated_code = "def helper():\n    x = 10\n    y = 20\n    z = x + y\n    return z\n"
    files = {
        "module_a.py": repeated_code,
        "module_b.py": repeated_code
    }

    res = detector.detect_duplicates(files)
    assert res["duplicate_count"] >= 1


def test_quality_score_calculation():
    """Test 5: QualityScoreCalculator sub-score aggregation and overall score out of 100."""
    calc = QualityScoreCalculator()

    scores = calc.calculate_scores(
        analysis_res={"average_complexity": 2.0},
        security_res={"security_score": 90.0},
        perf_res={"performance_score": 85.0},
        has_documentation=True
    )

    assert 80.0 <= scores["overall_score"] <= 100.0
    assert scores["security_score"] == 90.0
    assert scores["performance_score"] == 85.0


def test_auto_fix_pipeline_and_api_endpoints():
    """Test 6: Auto-Fix Pipeline execution and quality API endpoints."""
    rep_gen = QualityReportGenerator()

    files = {
        "main.py": "from fastapi import FastAPI   \n\n\napp = FastAPI()\n"
    }

    fixed = rep_gen.apply_autofix(files)
    assert "AIForge Auto-Formatted Module" in fixed["main.py"]

    # Test GET /api/quality-report/{project_id}
    res_rep = client.get("/api/quality-report/qual_test_01")
    assert res_rep.status_code == 200
    data_rep = res_rep.json()
    assert "scores" in data_rep
    assert data_rep["scores"]["overall_score"] > 0

    # Test POST /api/optimize/{project_id}
    res_opt = client.post("/api/optimize/qual_test_01")
    assert res_opt.status_code == 200
    assert res_opt.json()["status"] == "success"
