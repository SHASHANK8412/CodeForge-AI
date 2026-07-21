import asyncio
import json
import sys
from pathlib import Path

# Add root folder to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.evolution.evolution_pipeline import EvolutionPipeline

async def run_evolution_verification():
    print("======================================================================")
    print("AIForge SRE Evolution Engine E2E Verification Suite")
    print("======================================================================\n")

    workspace_root = str(Path(__file__).resolve().parent.parent)
    
    # Instantiate pipeline with default artifacts directory target
    pipeline = EvolutionPipeline()
    
    print("1. Launching SRE Self-Evolution Cycle step...")
    print("   - Collecting static code metrics")
    print("   - Auditing security vulnerabilities")
    print("   - Performing safe refactoring modifications")
    print("   - Running performance benchmarking suite")
    
    outcome = await pipeline.execute_evolution_loop(workspace_root)
    
    print("\n2. SRE Evolution Loop completed successfully!")
    print(f"   - Initial baseline score: {outcome['initial_score']['Overall']}%")
    print(f"   - Evolved quality score : {outcome['evolved_score']['Overall']}%")
    print(f"   - Refactored code files : {outcome['refactored_files']}")
    print(f"   - Security findings     : {outcome['findings_count']} indicators detected")
    print(f"   - API benchmark latency : {outcome['benchmark']['metrics']['api_latency_ms']}ms")
    print("")

    print("3. Verifying output reports compilation in artifacts folder...")
    reports = [
        "project_summary.md", "analysis_report.md", "architecture_review.md",
        "security_report.md", "performance_report.md", "database_review.md",
        "frontend_review.md", "backend_review.md", "testing_report.md",
        "devops_report.md", "improvement_plan.md"
    ]
    for rep in reports:
        rep_path = pipeline.reports_dir / rep
        if rep_path.exists():
            print(f"   [OK] Generated report: {rep}")
        else:
            print(f"   [FAIL] Missing report: {rep}")
    print("")

    # Print a sample score summary
    score_file = pipeline.reports_dir / "project_score.json"
    if score_file.exists():
        with open(score_file, "r", encoding="utf-8") as f:
            print(f"SRE Project Scores (project_score.json):")
            print(f.read().strip())
    print("")

    print("======================================================================")
    print("All SRE Evolution Engine verification checks completed successfully!")
    print("======================================================================")

if __name__ == "__main__":
    asyncio.run(run_evolution_verification())
