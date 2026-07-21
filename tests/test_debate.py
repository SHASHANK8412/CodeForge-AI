import pytest
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import patch
from backend.debate.orchestrator import DebateOrchestrator
from backend.debate.memory import DebateMemory
from backend.debate.critique import CritiqueEvaluator
from backend.debate.moderator import DebateModerator
from backend.graph.debate_graph import DebateGraphVisualizer

@pytest.mark.anyio
async def test_debate_orchestrator(tmp_path):
    orchestrator = DebateOrchestrator(memory_dir=str(tmp_path / "memory"))
    
    # Mock LLM calls for proposals and critiques to make it synchronous and fast
    mock_proposal = {
        "choice": "REST",
        "confidence": 95.0,
        "summary": "Mock FastAPI router",
        "advantages": "High performance",
        "disadvantages": "None",
        "potential_risks": "Minimal"
    }

    with patch("backend.debate.orchestrator.generate_text", return_value='{"choice": "REST", "confidence": 95.0}'):
        with patch("backend.debate.critique.generate_text", return_value="Security is compliant"):
            result = await orchestrator.run_debate(
                prompt="Build a CRUD App using React and FastAPI",
                participants=["architect", "backend", "frontend", "database"]
            )
            
            assert "winning_solution" in result
            assert result["winning_solution"] == "REST"
            assert len(result["rounds_history"]) == 2

def test_debate_memory(tmp_path):
    mem = DebateMemory(memory_dir=str(tmp_path))
    
    session = {
        "prompt": "Build an E-commerce Website",
        "winning_solution": "REST + SQL",
        "reasoning": "High scalability and transactions support"
    }
    
    saved_path = mem.save_debate("E-commerce Website", session)
    assert Path(saved_path).exists()

    # Similar lookup
    match = mem.lookup_similar_debate("Create an E-commerce store using react")
    assert match["winning_solution"] == "REST + SQL"

def test_debate_moderator():
    moderator = DebateModerator()
    
    round_ops = {
        "backend": {"choice": "REST", "confidence": 95.0},
        "frontend": {"choice": "GraphQL", "confidence": 80.0}
    }
    summary = moderator.summarize_round(1, round_ops)
    assert "Backend" in summary
    assert "REST" in summary

    # Verify circular detection
    history = [
        {"backend": {"choice": "REST"}, "frontend": {"choice": "GraphQL"}},
        {"backend": {"choice": "REST"}, "frontend": {"choice": "GraphQL"}},
        {"backend": {"choice": "REST"}, "frontend": {"choice": "GraphQL"}}
    ]
    assert moderator.detect_circular_discussion(history) is True

def test_debate_graph_visualizer(tmp_path):
    output_json = tmp_path / "debate_graph.json"
    visualizer = DebateGraphVisualizer(output_path=str(output_json))
    
    graph_data = visualizer.generate_and_save_graph(
        participants=["backend", "frontend"],
        votes={"backend": "REST", "frontend": "GraphQL"},
        consensus="REST"
    )
    
    assert output_json.exists()
    assert len(graph_data["nodes"]) == 6
    assert graph_data["consensus_choice"] == "REST"
