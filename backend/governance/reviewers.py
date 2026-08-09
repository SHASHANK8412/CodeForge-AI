"""
AIForge Reviewer Manager
========================
Tracks reviewer assignments, capacity, workload distribution, and review SLA metrics.
"""

from typing import Dict, Any, List, Optional


class ReviewerManager:
    """
    Manages reviewer pool and active review assignments.
    """

    def __init__(self) -> None:
        self.reviewers: Dict[str, Dict[str, Any]] = {
            "rev_1": {
                "reviewer_id": "rev_1",
                "name": "Dr. Sarah Connor",
                "role": "Lead Architect",
                "email": "sarah.connor@aiforge.dev",
                "status": "active",
                "active_reviews": 2,
                "completed_reviews": 34,
                "avg_response_time_minutes": 18
            },
            "rev_2": {
                "reviewer_id": "rev_2",
                "name": "Alex Mercer",
                "role": "Security Lead",
                "email": "alex.mercer@aiforge.dev",
                "status": "active",
                "active_reviews": 1,
                "completed_reviews": 28,
                "avg_response_time_minutes": 12
            }
        }

    def get_all_reviewers(self) -> List[Dict[str, Any]]:
        return list(self.reviewers.values())

    def assign_reviewer(self, reviewer_id: str, request_id: str) -> Dict[str, Any]:
        if reviewer_id in self.reviewers:
            rev = self.reviewers[reviewer_id]
            rev["active_reviews"] += 1
            return {"reviewer": rev, "request_id": request_id}
        raise ValueError(f"Reviewer ID '{reviewer_id}' not found.")

    def complete_review(self, reviewer_id: str) -> Dict[str, Any]:
        if reviewer_id in self.reviewers:
            rev = self.reviewers[reviewer_id]
            rev["active_reviews"] = max(0, rev["active_reviews"] - 1)
            rev["completed_reviews"] += 1
            return rev
        raise ValueError(f"Reviewer ID '{reviewer_id}' not found.")


global_reviewer_manager = ReviewerManager()
