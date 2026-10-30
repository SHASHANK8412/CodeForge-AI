"""
The reviewer's output is checked, not trusted: an unreadable review is NOT_REVIEWED (it used to become a passing
85/100), a finding about a file that is not in the project is unverified and never blocking, and a review that only
repeats the old prompt example is not a review. The prompt no longer contains concrete values to copy.
"""

import json

from backend.agents.reviewer_agent import ReviewerAgent

FILES = {"backend/main.py": "app = None\n", "frontend/src/App.jsx": "export default 1\n"}


def test_unreadable_output_is_not_a_passing_review():
    r = ReviewerAgent().parse_review_json("Looks great to me!")
    assert r["overall_status"] == "NOT_REVIEWED" and r["overall_score"] is None and r["findings"] == []


def test_findings_must_name_files_that_exist():
    review = {"overall_score": 70, "gates": {}, "findings": [
        {"severity": "HIGH", "file": "backend/main.py", "message": "real", "blocking": True},
        {"severity": "CRITICAL", "file": "backend/routes/payments.py", "message": "invented", "blocking": True}]}
    out = ReviewerAgent.validate_review(review, FILES)
    assert [f["message"] for f in out["findings"]] == ["real"]
    assert out["unverified_findings"][0]["message"] == "invented" and out["unverified_findings"][0]["blocking"] is False


def test_a_copied_prompt_example_is_rejected():
    copied = {"overall_score": 91, "gates": {}, "findings": [
        {"severity": "HIGH", "file": "backend/routes/auth.py", "line": 42, "message": "Authentication input is not validated"}]}
    out = ReviewerAgent.validate_review(copied, FILES)
    assert out["overall_status"] == "NOT_REVIEWED" and out["overall_score"] is None


def test_the_prompt_has_a_schema_not_values_to_copy():
    prompt = ReviewerAgent().system_prompt
    assert "backend/routes/auth.py" not in prompt and '"overall_score": 91' not in prompt
    assert "<integer 0-100" in prompt


def test_the_workflow_scores_verified_findings(monkeypatch):
    import asyncio
    from backend.graph import parallel_workflow as wf
    reply = json.dumps({"overall_score": 99, "gates": {}, "findings": [
        {"severity": "HIGH", "file": "backend/main.py", "message": "x"},
        {"severity": "MEDIUM", "file": "frontend/src/App.jsx", "message": "y"},
        {"severity": "CRITICAL", "file": "not/in/project.py", "message": "z"}]})

    async def fake(*_a, **_k):
        return reply
    monkeypatch.setattr(wf.reviewer_agent, "run_async", fake)
    out = asyncio.run(wf.reviewer_node({"files": FILES, "duplicate_report": {}}))
    review = out["review"]
    assert review["status"] == "REVIEWED" and review["score"] == 85.0, "100 - 10 (high) - 5 (medium); the model's 99 is ignored"
    assert len(review["unverified_findings"]) == 1

    async def garbage(*_a, **_k):
        return "no json here"
    monkeypatch.setattr(wf.reviewer_agent, "run_async", garbage)
    out = asyncio.run(wf.reviewer_node({"files": FILES, "duplicate_report": {}}))
    assert out["review"]["status"] == "NOT_REVIEWED" and out["review"]["score"] is None
