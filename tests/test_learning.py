import pytest
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock
from backend.learning.learning_memory import LearningMemory
from backend.learning.experience_db import ExperienceDatabase
from backend.learning.pattern_recognizer import PatternRecognizer
from backend.learning.prompt_optimizer import PromptOptimizer
from backend.learning.best_practices import BestPracticesGenerator
from backend.learning.performance_tracker import PerformanceTracker
from backend.learning.architecture_evolver import ArchitectureEvolver
from backend.learning.confidence_scorer import ConfidenceScorer
from backend.learning.reflection_engine import ReflectionEngine
from backend.learning.learning_pipeline import LearningPipeline

def test_learning_memory(tmp_path):
    mem = LearningMemory(memory_dir=str(tmp_path))
    
    summary = {
        "project": "Todo-App",
        "timestamp": 12345.0,
        "technologies": ["React", "FastAPI"],
        "mistakes": [],
        "fixes": [],
        "best_practices": {},
        "performance": {},
        "deployment_notes": "All OK",
        "final_score": 98
    }

    # Save
    path = mem.save_project_summary("Todo-App", summary)
    assert Path(path).exists()

    # Load
    loaded = mem.load_project_summary("Todo-App")
    assert loaded["project"] == "Todo-App"
    assert loaded["final_score"] == 98

    # List all
    all_sums = mem.get_all_summaries()
    assert len(all_sums) == 1

def test_experience_db(tmp_path):
    mem = LearningMemory(memory_dir=str(tmp_path))
    db = ExperienceDatabase(memory=mem)
    
    # Save a past project
    mem.save_project_summary("E-Commerce", {
        "project": "E-Commerce",
        "technologies": ["React", "FastAPI", "PostgreSQL"],
        "best_practices": {"folder_structure": ["src/commerce"], "security_practices": ["JWT"]},
        "deployment_notes": "Docker build passed",
        "final_score": 95
    })

    # Search match
    rec = db.get_reuse_recommendation("Build an E-Commerce store using React and FastAPI")
    assert rec["similar_project_found"] is True
    assert rec["project_name"] == "E-Commerce"
    assert "JWT" in rec["suggested_auth_schema"]

    # Search miss
    no_rec = db.get_reuse_recommendation("Create simple script for parsing CSV files")
    assert no_rec["similar_project_found"] is False

def test_pattern_recognizer(tmp_path):
    mem = LearningMemory(memory_dir=str(tmp_path))
    rec = PatternRecognizer(memory=mem, patterns_dir=str(tmp_path))

    # Seed summary
    mem.save_project_summary("Shop", {
        "project": "Shop",
        "technologies": ["React", "FastAPI"],
        "mistakes": ["circular_import"],
        "final_score": 90
    })

    patterns = rec.analyze_patterns()
    assert "frequent_stacks" in patterns
    assert patterns["frequent_stacks"][0]["stack"] == "FastAPI + React"
    assert patterns["repeated_mistakes"]["circular_import"] == 1

def test_prompt_optimizer(tmp_path):
    opt = PromptOptimizer(prompts_dir=str(tmp_path))
    
    # Verify default creation
    assert (tmp_path / "backend.txt").exists()
    
    default_p = opt.get_system_prompt("backend", "fallback")
    assert "FastAPI" in default_p

    # Test optimization patch
    with patch("backend.learning.prompt_optimizer.generate_text", return_value="Write clean modular python views"):
        optimized = opt.optimize_prompt("backend", "Backend is weak")
        assert optimized == "Write clean modular python views"
        
        # Verify saved to disk
        disk_p = opt.get_system_prompt("backend", "")
        assert disk_p == "Write clean modular python views"

def test_best_practices_generator(tmp_path):
    gen = BestPracticesGenerator(knowledge_dir=str(tmp_path))
    assert (tmp_path / "best_practices.md").exists()

    summary = {
        "project": "App",
        "technologies": ["Vue", "FastAPI"],
        "final_score": 90,
        "best_practices": {
            "folder_structure": ["src/"],
            "security_practices": ["JWT"],
            "api_design": ["Standard REST"]
        }
    }
    content = gen.update_best_practices(summary)
    assert "Project Insight: App" in content

def test_performance_tracker(tmp_path):
    tracker = PerformanceTracker(analytics_dir=str(tmp_path))
    
    metrics = {
        "generation_time": 200.0,
        "llm_tokens": 60000,
        "failures_count": 1,
        "retries_count": 0,
        "memory_usage_mb": 600.0
    }
    recs = tracker.track_performance(metrics)
    assert len(recs) >= 4
    assert any("generation time" in r for r in recs)

def test_architecture_evolver(tmp_path):
    mem = LearningMemory(memory_dir=str(tmp_path))
    ev = ArchitectureEvolver(memory=mem, knowledge_dir=str(tmp_path))

    # Add two projects adopting Postgres
    mem.save_project_summary("P1", {"technologies": ["PostgreSQL"]})
    mem.save_project_summary("P2", {"technologies": ["PostgreSQL"]})

    recs = ev.evolve_architecture()
    assert any("postgresql" in r.lower() for r in recs)
    assert (tmp_path / "architecture_recommendations.md").exists()

def test_confidence_scorer():
    scorer = ConfidenceScorer()
    # Fully successful
    s1 = scorer.calculate_confidence("main.py", review_passed=True, tests_passed=True, deployment_passed=True)
    assert s1 == 100.0
    
    # Degradations
    s2 = scorer.calculate_confidence("main.py", review_passed=False, tests_passed=False, deployment_passed=True)
    assert s2 < 50.0

def test_reflection_engine(tmp_path):
    eng = ReflectionEngine(reflection_dir=str(tmp_path))
    
    with patch("backend.learning.reflection_engine.generate_text", return_value="### Reflection Notes\nSuccess"):
        ref = eng.generate_reflection("Todo", ["React"], [], True)
        assert "Success" in ref
        assert (tmp_path / "reflection.md").exists()

@pytest.mark.anyio
async def test_learning_pipeline(tmp_path):
    # Mock files path under tmp_path
    with patch("backend.learning.learning_memory.Path") as mock_path:
        # Redirect constructor path resolves to tmp_path
        pipeline = LearningPipeline()
        
        # Override individual properties to avoid system filesystem touch
        pipeline.memory = LearningMemory(memory_dir=str(tmp_path / "memory"))
        pipeline.experience_db = ExperienceDatabase(memory=pipeline.memory)
        pipeline.pattern_recognizer = PatternRecognizer(memory=pipeline.memory, patterns_dir=str(tmp_path / "patterns"))
        pipeline.prompt_optimizer = PromptOptimizer(prompts_dir=str(tmp_path / "prompts"))
        pipeline.best_practices_gen = BestPracticesGenerator(knowledge_dir=str(tmp_path / "knowledge"))
        pipeline.performance_tracker = PerformanceTracker(analytics_dir=str(tmp_path / "analytics"))
        pipeline.architecture_evolver = ArchitectureEvolver(memory=pipeline.memory, knowledge_dir=str(tmp_path / "knowledge"))
        pipeline.reflection_engine = ReflectionEngine(reflection_dir=str(tmp_path / "reflection"))

        metrics = {"generation_time": 45.2, "llm_tokens": 1200, "failures_count": 0}
        
        # Mock LLM reflection call to run in tests fast
        with patch("backend.learning.reflection_engine.generate_text", return_value="### Reflection\nAll systems nominal"):
            res = await pipeline.execute_post_project_learning(
                project_name="BlogApp",
                technologies=["React", "FastAPI"],
                execution_metrics=metrics,
                reviewer_feedback="",
                syntax_errors=0
            )
            assert res["success"] is True
            assert res["confidence_score"] == 100.0
            assert "All systems nominal" in res["reflection"]
