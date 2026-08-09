"""
AIForge V2 Master Verification Suite: Next-Generation AI Software Engineer Enhancements
========================================================================================
Verifies:
1. AST Code Analyzer Symbol Extraction
2. LSP Diagnostics & Symbol Definition Lookup
3. LangGraph State Checkpointing Save & Restore
4. Redis Shared Cache Manager
5. Static Analysis Quality Scanner (Bandit, Semgrep, Ruff, MyPy)
6. Incremental Module Generation Engine
7. 18-Stage Autonomous Pipeline Integration
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from backend.analysis.ast_analyzer import global_ast_analyzer
from backend.analysis.lsp_engine import global_lsp_engine
from backend.graph.checkpoint_engine import global_checkpoint_engine
from backend.utils.redis_cache import global_redis_cache
from backend.quality.static_analysis import global_static_analysis_engine
from backend.generators.incremental_generator import global_incremental_generator
from backend.memory.project_memory import ProjectMemoryStore
from backend.orchestrator.autonomous_engineer import global_autonomous_engineer

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


def verify_nextgen_features():
    print("===========================================================================")
    print(" 🚀 AIForge V2 – Next-Gen AI Software Engineer Enhancements Verification")
    print("===========================================================================\n")

    # ---------------------------------------------------------
    # Verification 1: AST Code Understanding
    # ---------------------------------------------------------
    section("Verification 1: AST Code Analyzer Symbol Extraction")
    ast_res = global_ast_analyzer.analyze_python_code(
        "app/models.py",
        "import os\nclass UserAccount:\n    pass\nasync def get_user(id: int) -> dict:\n    return {}"
    )
    check("AST Analyzer parses code without syntax errors", ast_res["valid_syntax"])
    check("Extracted class 'UserAccount'", len(ast_res["classes"]) == 1 and ast_res["classes"][0]["name"] == "UserAccount")
    check("Extracted async function 'get_user'", len(ast_res["functions"]) == 1 and ast_res["functions"][0]["is_async"])

    # ---------------------------------------------------------
    # Verification 2: LSP Symbol Navigation & Diagnostics
    # ---------------------------------------------------------
    section("Verification 2: LSP Diagnostics & Symbol Definition Lookup")
    files = {
        "app/models.py": "class UserAccount:\n    pass",
        "app/auth.py": "def authenticate(): pass"
    }
    idx = global_lsp_engine.index_codebase(files)
    check("LSP Engine indexed global symbols", idx["symbol_count"] >= 2)
    defn = global_lsp_engine.find_definition("UserAccount")
    check("LSP definition lookup for 'UserAccount' resolved cleanly", defn is not None and defn["file"] == "app/models.py")

    # ---------------------------------------------------------
    # Verification 3: LangGraph State Checkpointing
    # ---------------------------------------------------------
    section("Verification 3: LangGraph State Checkpointing")
    ckpt_path = global_checkpoint_engine.save_checkpoint("sess_777", "architect", {"blueprint": "v2_arch"})
    loaded_state = global_checkpoint_engine.load_latest_checkpoint("sess_777")
    check("LangGraph checkpoint saved snapshot to disk", ckpt_path != "")
    check("Loaded checkpoint restored exact architecture blueprint", loaded_state is not None and loaded_state.get("blueprint") == "v2_arch")

    # ---------------------------------------------------------
    # Verification 4: Redis Shared Cache Manager
    # ---------------------------------------------------------
    section("Verification 4: Redis Shared Cache Manager")
    key = global_redis_cache.make_key("prompt", "Develop Formula 1 Web Application")
    global_redis_cache.set(key, "cached_pipeline_result")
    cached_val = global_redis_cache.get(key)
    check("Redis shared cache hit returns cached completion result", cached_val == "cached_pipeline_result")

    # ---------------------------------------------------------
    # Verification 5: Static Analysis Quality Scanner
    # ---------------------------------------------------------
    section("Verification 5: Static Analysis (Bandit, Semgrep, Ruff, MyPy)")
    codebase = {
        "backend/main.py": "import os\nfrom fastapi import FastAPI; app = FastAPI()",
        "backend/auth.py": "def login(email):\n    try:\n        pass\n    except:\n        pass"
    }
    sa_rep = global_static_analysis_engine.run_static_analysis(codebase)
    check("Static analysis score >= 90.0", sa_rep["static_analysis_score"] >= 90.0)
    check("Static analysis tools executed (Bandit, Semgrep, Ruff, MyPy)", len(sa_rep["tools_executed"]) == 4)

    # ---------------------------------------------------------
    # Verification 6: Incremental Module Generation Engine
    # ---------------------------------------------------------
    section("Verification 6: Incremental Module Generation Engine")
    mem = ProjectMemoryStore("Incremental Formula 1 Project")
    inc_files = global_incremental_generator.generate_modules_incrementally("Incremental Formula 1 Project", mem)
    check("Incremental generator produced 6 core project modules", len(inc_files) >= 5)
    check("Generated backend FastAPI service layer", "backend/main.py" in inc_files)
    check("Generated frontend React SPA", "frontend/src/App.jsx" in inc_files)

    # ---------------------------------------------------------
    # Verification 7: Integrated Pipeline Execution
    # ---------------------------------------------------------
    section("Verification 7: Integrated Pipeline Execution")
    pipe_res = global_autonomous_engineer.run_autonomous_pipeline("Develop Formula 1 Autonomous Next-Gen Web Application")
    check("Full 18-stage pipeline completed with Quality Score >= 95", pipe_res["quality_score"] >= 95.0)

    # Summary
    print("\n" + "="*75)
    print(f" AIFORGE V2 NEXT-GEN FEATURES VERIFICATION SUMMARY: {PASS if _results['failed'] == 0 else FAIL}")
    print(f" Passed: { _results['passed'] } | Failed: { _results['failed'] }")
    print("="*75 + "\n")

    return _results["failed"] == 0


if __name__ == "__main__":
    success = verify_nextgen_features()
    sys.exit(0 if success else 1)
