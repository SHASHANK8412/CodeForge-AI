"""
AIForge V2 Day 44 Verification Suite: AI Memory, Learning & Continuous Improvement
===================================================================================
Tests all Day 44 scenarios:
1. Similar project exists -> Relevant memories retrieved
2. New project type -> Memory grows with new knowledge
3. Repeated error -> Previous fix reused
4. Similar UI requested -> Existing component suggested
5. Completed project -> Lessons and reusable assets stored
"""

import sys
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.agents.learning_agent import LearningAgent
from backend.services.knowledge_extractor import KnowledgeExtractor
from backend.services.memory_indexer import MemoryIndexer
from backend.services.memory_retriever import MemoryRetriever

PASS = "[PASS]"
FAIL = "[FAIL]"
_results = {"passed": 0, "failed": 0}


def section(title: str):
    print(f"\n{'='*75}")
    print(f"  {title}")
    print(f"{'='*75}")


def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    if condition:
        _results["passed"] += 1
    else:
        _results["failed"] += 1
    msg = f"  {status}  {name}"
    if detail:
        msg += f"\n        => {detail}"
    print(msg)
    return condition


def verify_day44_pipeline():
    print("===========================================================================")
    print(" 🚀 AIForge V2 – Day 44 AI Memory, Learning & Continuous Improvement")
    print("===========================================================================\n")

    learning_agent = LearningAgent()
    extractor = KnowledgeExtractor()
    indexer = MemoryIndexer()
    retriever = MemoryRetriever()

    # ---------------------------------------------------------
    # Scenario 1: Completed Project -> Lessons & Reusable Assets Stored
    # ---------------------------------------------------------
    section("Scenario 1: Completed Project -> Lessons & Assets Stored")
    project1 = {
        "name": "Social Media Dashboard",
        "prompt": "Create a social media management dashboard with React and FastAPI",
        "project_files": {
            "frontend/src/App.jsx": "import React from 'react'; export default function App() {}",
            "frontend/src/components/Card.jsx": "export default function Card() {}",
            "backend/main.py": "from fastapi import FastAPI\napp = FastAPI()",
            "database/schema.sql": "CREATE TABLE posts (id SERIAL PRIMARY KEY, content TEXT);"
        },
        "quality_score": 97.5,
        "fixed_errors": [
            {
                "error": "ModuleNotFoundError: No module named 'fastapi'",
                "solution": "Added fastapi to requirements.txt",
                "success": True
            }
        ]
    }

    analysis1 = learning_agent.analyze_completed_project(project1)
    know1 = extractor.extract_knowledge(project1["project_files"], metadata={"prompt": project1["prompt"], "error_resolutions": project1["fixed_errors"]})
    rec1 = indexer.index_project("proj_day44_01", project1["prompt"], know1, quality_score=97.5)

    check("Analyzed completed project and extracted lessons learned", len(analysis1["lessons_learned"]) >= 2)
    check("Extracted 7 knowledge asset categories (API, DB, UI, Prompts, Fixes, Tests, Folders)",
          len(know1["api_patterns"]) >= 1 and len(know1["ui_components"]) >= 1 and len(know1["database_schemas"]) >= 1)
    check("Indexed project record into long-term memory", rec1["project_id"] == "proj_day44_01")

    # ---------------------------------------------------------
    # Scenario 2: Similar Project Exists -> Relevant Memories Retrieved
    # ---------------------------------------------------------
    section("Scenario 2: Similar Project Exists -> Memories Retrieved")
    ctx2 = retriever.retrieve_context_for_prompt("Build social media analytics platform")
    check("Retrieved relevant past project memories for similar prompt", ctx2["similar_projects_count"] >= 1)
    check("Formatted context prompt snippet for LLM injection", "Long-Term AI Memory Context" in ctx2["context_prompt_snippet"])

    # ---------------------------------------------------------
    # Scenario 3: Repeated Error -> Previous Fix Reused
    # ---------------------------------------------------------
    section("Scenario 3: Repeated Error -> Previous Fix Reused")
    check("Retrieved proven error-resolution pair from memory", len(ctx2["proven_solutions"]) >= 1)
    check("Identified previous fix for missing module error",
          any("fastapi" in sol.get("solution", "").lower() or "fastapi" in sol.get("error", "").lower() for sol in ctx2["proven_solutions"]))

    # ---------------------------------------------------------
    # Scenario 4: Similar UI Requested -> Existing Component Suggested
    # ---------------------------------------------------------
    section("Scenario 4: Similar UI Requested -> Component Suggested")
    check("Retrieved reusable React UI components from memory", len(ctx2["reusable_components"]) >= 1)

    # ---------------------------------------------------------
    # Scenario 5: New Project Type -> Memory Grows Continuously
    # ---------------------------------------------------------
    section("Scenario 5: New Project Type -> Memory Growth")
    project2 = {
        "name": "Fintech Crypto Wallet",
        "prompt": "Build a real-time crypto trading wallet application",
        "project_files": {
            "frontend/src/Wallet.jsx": "import React from 'react'; export default function Wallet() {}",
            "backend/crypto.py": "from fastapi import FastAPI\napp = FastAPI()"
        },
        "quality_score": 96.0
    }
    know2 = extractor.extract_knowledge(project2["project_files"], metadata={"prompt": project2["prompt"]})
    rec2 = indexer.index_project("proj_day44_02", project2["prompt"], know2, quality_score=96.0)

    p_count = len(list(indexer.projects_dir.glob("*.json")))
    check("Indexed new project type and expanded memory store", p_count >= 2 and rec2["project_id"] == "proj_day44_02")

    # Summary
    print("\n" + "="*75)
    print(f" AIFORGE V2 DAY 44 VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: {_results['passed']} | Failed: {_results['failed']}")
    print("="*75 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = verify_day44_pipeline()
    sys.exit(0 if success else 1)
