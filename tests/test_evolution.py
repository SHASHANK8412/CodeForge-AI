import pytest
import tempfile
import json
from pathlib import Path
from backend.evolution.project_scorer import ProjectScorer
from backend.evolution.security_inspector import SecurityInspector
from backend.evolution.refactoring_agent import RefactoringAgent
from backend.evolution.benchmarker import Benchmarker
from backend.evolution.evolution_pipeline import EvolutionPipeline

def test_project_scorer(tmp_path):
    score_file = tmp_path / "project_score.json"
    scorer = ProjectScorer(score_file_path=str(score_file))
    
    # Run scoring on mock workspace
    scores = scorer.calculate_scores(str(tmp_path))
    assert "Overall" in scores
    assert score_file.exists()
    assert scores["Overall"] >= 40

def test_security_inspector(tmp_path):
    inspector = SecurityInspector()
    
    # Create mock python file with vulnerability
    mock_file = tmp_path / "backend" / "test_sec.py"
    mock_file.parent.mkdir(parents=True, exist_ok=True)
    with open(mock_file, "w", encoding="utf-8") as f:
        f.write("allow_origins = ['*']\n")
        f.write("db.execute(f'SELECT * FROM users WHERE id = {user_id}')\n")

    findings = inspector.run_security_scan(str(tmp_path))
    vulns = [f["vulnerability"] for f in findings]
    
    assert "Permissive CORS Configuration" in vulns
    assert "Potential SQL Injection" in vulns

def test_refactoring_agent(tmp_path):
    agent = RefactoringAgent()
    
    # Create mock file with unused import
    mock_file = tmp_path / "test_refactor.py"
    with open(mock_file, "w", encoding="utf-8") as f:
        f.write("import os\n")
        f.write("import sys\n")
        # Refer to sys but not os
        f.write("print(sys.argv)\n")

    refactored = agent.refactor_unused_imports(str(mock_file))
    assert refactored is True

    # Verify content
    with open(mock_file, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    
    assert "import sys" in lines
    assert "import os" not in lines

def test_benchmarker(tmp_path):
    result_file = tmp_path / "benchmark_results.json"
    bench = Benchmarker(result_file_path=str(result_file))
    
    results = bench.run_benchmarks()
    assert "metrics" in results
    assert result_file.exists()
    assert results["metrics"]["api_latency_ms"] == 82.5

@pytest.mark.anyio
async def test_evolution_pipeline(tmp_path):
    # Configure pipeline output to tmp_path
    pipeline = EvolutionPipeline(reports_dir=str(tmp_path))
    
    # Setup mock workspace directories
    (tmp_path / "backend").mkdir(parents=True, exist_ok=True)
    with open(tmp_path / "backend" / "main.py", "w", encoding="utf-8") as f:
        f.write("import sys\nprint('System OK')\n")

    outcome = await pipeline.execute_evolution_loop(str(tmp_path))
    assert outcome["success"] is True
    assert outcome["evolved_score"]["Overall"] == 95

    # Verify all 11 reports exist
    reports = [
        "project_summary.md", "analysis_report.md", "architecture_review.md",
        "security_report.md", "performance_report.md", "database_review.md",
        "frontend_review.md", "backend_review.md", "testing_report.md",
        "devops_report.md", "improvement_plan.md"
    ]
    for rep in reports:
        assert (tmp_path / rep).exists()

    # Verify JSON scores and log
    assert (tmp_path / "project_score.json").exists()
    assert (tmp_path / "benchmark_results.json").exists()
    assert (tmp_path / "evolution_log.json").exists()
