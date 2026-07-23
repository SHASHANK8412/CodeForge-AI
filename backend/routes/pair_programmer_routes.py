"""
FastAPI Routes for Day 72 Autonomous Pair Programmer
=====================================================
Exposes REST endpoints for interactive code editing, repo analysis, and patch previews.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from backend.agents.pair_programmer_agent import PairProgrammerAgent

router = APIRouter(prefix="/api/v1/pair-programmer", tags=["Pair Programmer Agent"])
pair_programmer = PairProgrammerAgent()

class PairEditRequest(BaseModel):
    workspace_path: str
    prompt: str
    apply_changes: Optional[bool] = True

@router.post("/edit")
async def process_pair_edit(req: PairEditRequest) -> Dict[str, Any]:
    """Processes interactive pair programming request, returning repo analysis, patches, and explanations."""
    try:
        res = pair_programmer.process_pair_request(req.workspace_path, req.prompt, apply_changes=req.apply_changes)
        return {"status": "success", "result": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_repo(req: PairEditRequest) -> Dict[str, Any]:
    """Performs static repository analysis and context file selection."""
    try:
        analysis = pair_programmer.repo_agent.analyze_repository(req.workspace_path)
        relevant = pair_programmer.repo_agent.select_relevant_context(analysis, req.prompt)
        return {"status": "success", "analysis": analysis, "relevant_files": relevant}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
