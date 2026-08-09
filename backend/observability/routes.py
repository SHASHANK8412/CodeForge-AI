from fastapi import APIRouter, Depends, HTTPException, status
from backend.auth.dependencies import get_current_user
from backend.observability.telemetry import global_observability_telemetry
from backend.observability.evaluator import global_evaluation_engine
from backend.observability.feedback import (
    FeedbackSubmissionRequest,
    submit_user_feedback,
    get_project_feedback
)

router = APIRouter(tags=["Observability, Evaluation & Reliability"])


@router.get("/api/admin/observability")
def get_observability_dashboard_data(current_user: dict = Depends(get_current_user)):
    """Returns telemetry metrics, health probes, agent timings, error counts, and parallel efficiency."""
    return global_observability_telemetry.get_dashboard_telemetry()


@router.get("/api/admin/evaluations")
def get_evaluations_center_data(current_user: dict = Depends(get_current_user)):
    """Returns benchmark dataset, evaluation metrics, regression deltas, and agent scores."""
    return global_evaluation_engine.get_evaluation_data()


@router.post("/api/feedback")
def submit_feedback_endpoint(req: FeedbackSubmissionRequest, current_user: dict = Depends(get_current_user)):
    """Submits human quality rating & feedback for a project generation."""
    entry = submit_user_feedback(current_user["id"], req)
    return {"success": True, "feedback": entry}


@router.get("/api/feedback/{project_id}")
def get_project_feedback_endpoint(project_id: str):
    """Returns feedback records for a given project."""
    return {"feedback": get_project_feedback(project_id)}
