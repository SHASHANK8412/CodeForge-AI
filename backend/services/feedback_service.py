"""
AIForge Day 101 Feedback Service & Sentiment Analyzer
======================================================
1. Feedback Analyzer: Categorizes user feedback into High, Medium, and Low priorities.
2. Sentiment Analysis: Classifies feedback into Positive, Negative, Neutral, or Urgent.
3. Duplicate Issue Detection: Merges semantic duplicates (e.g. 'Login broken' & 'Can't sign in').
4. Business Value Scoring: Calculates Business Impact, Technical Complexity, Revenue Potential, User Satisfaction, and Maintenance Cost.
"""

import math
import logging
from typing import Dict, Any, List, Optional

_logger = logging.getLogger("aiforge.services.feedback")


class FeedbackService:
    """
    Feedback Analyzer, Sentiment Analysis & Duplicate Issue Detector.
    """

    def analyze_sentiment(self, text: str) -> Dict[str, str]:
        t_lower = text.lower()
        if any(w in t_lower for w in ["crash", "broken", "critical", "urgent", "cannot", "can't", "fail"]):
            sentiment = "Negative"
            urgency = "Urgent"
        elif any(w in t_lower for w in ["slow", "lag", "needed", "missing", "confusing"]):
            sentiment = "Negative"
            urgency = "Normal"
        elif any(w in t_lower for w in ["great", "love", "awesome", "good", "perfect"]):
            sentiment = "Positive"
            urgency = "Low"
        else:
            sentiment = "Neutral"
            urgency = "Normal"

        return {
            "sentiment": sentiment,
            "urgency": urgency
        }

    def detect_duplicate_issues(self, issues: List[str]) -> List[Dict[str, Any]]:
        _logger.info(f"FeedbackService: Scanning {len(issues)} issues for semantic duplicates...")
        unique_groups = []
        seen = set()

        for idx, issue in enumerate(issues):
            if idx in seen:
                continue

            duplicates = []
            words1 = set(issue.lower().split())

            for idx2, issue2 in enumerate(issues[idx+1:], idx+1):
                if idx2 in seen:
                    continue
                words2 = set(issue2.lower().split())
                overlap = len(words1.intersection(words2)) / max(1, len(words1.union(words2)))

                # Keyword overlap or known semantic aliases (e.g. login / sign in)
                is_alias = ("login" in issue.lower() and ("sign in" in issue2.lower() or "signin" in issue2.lower()))
                if overlap > 0.4 or is_alias:
                    duplicates.append(issue2)
                    seen.add(idx2)

            seen.add(idx)
            unique_groups.append({
                "primary_issue": issue,
                "merged_duplicates": duplicates,
                "merged_count": len(duplicates) + 1
            })

        return unique_groups

    def calculate_business_value(self, feature_name: str) -> Dict[str, Any]:
        f_lower = feature_name.lower()
        if "login" in f_lower or "crash" in f_lower or "auth" in f_lower:
            impact, complexity, revenue, sat, cost = 9, 3, 8, 9, 2
            priority = "High"
        elif "dark mode" in f_lower or "theme" in f_lower:
            impact, complexity, revenue, sat, cost = 8, 2, 6, 9, 1
            priority = "High"
        elif "notification" in f_lower or "alert" in f_lower:
            impact, complexity, revenue, sat, cost = 7, 4, 7, 8, 3
            priority = "Medium"
        else:
            impact, complexity, revenue, sat, cost = 5, 5, 5, 6, 4
            priority = "Low"

        score = round((impact * 0.35 + revenue * 0.25 + sat * 0.25) / max(1, complexity * 0.15), 1)

        return {
            "feature": feature_name,
            "business_impact": f"{impact}/10",
            "technical_complexity": f"{complexity}/10",
            "revenue_potential": f"{revenue}/10",
            "user_satisfaction": f"{sat}/10",
            "maintenance_cost": f"{cost}/10",
            "overall_priority": priority,
            "value_score": score
        }

    def categorize_feedback(self, feedback_list: List[str]) -> Dict[str, Any]:
        high_priority = []
        medium_priority = []
        low_priority = []

        for item in feedback_list:
            analysis = self.analyze_sentiment(item)
            bv = self.calculate_business_value(item)
            entry = {
                "feedback": item,
                "sentiment": analysis["sentiment"],
                "urgency": analysis["urgency"],
                "business_value": bv
            }

            if analysis["urgency"] == "Urgent" or bv["overall_priority"] == "High":
                high_priority.append(entry)
            elif bv["overall_priority"] == "Medium":
                medium_priority.append(entry)
            else:
                low_priority.append(entry)

        return {
            "high_priority": high_priority,
            "medium_priority": medium_priority,
            "low_priority": low_priority,
            "summary": {
                "high_count": len(high_priority),
                "medium_count": len(medium_priority),
                "low_count": len(low_priority)
            }
        }


global_feedback_service = FeedbackService()
