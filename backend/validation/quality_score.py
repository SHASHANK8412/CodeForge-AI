import logging
from typing import List, Dict
from backend.validation.models import QualityScore, ValidationResult

_logger = logging.getLogger("aiforge.performance")

class QualityScoreCalculator:
    """
    Computes weighted quality scores and grades for validated code bases.
    """

    def __init__(self) -> None:
        self.weights = {
            "Syntax Checker": 0.25,
            "Security Checker": 0.20,
            "Performance Checker": 0.15,
            "Architecture Checker": 0.15,
            "API Checker": 0.10,
            "Frontend Checker": 0.05,
            "Database Checker": 0.05,
            "Documentation Checker": 0.05
        }

    def compute_score(self, results: List[ValidationResult], has_docs: bool = True) -> QualityScore:
        _logger.info("Computing final quality score...")
        
        # Build score lookup map, fallback to 100.0 if not run
        scores = {k: 100.0 for k in self.weights.keys()}
        
        # Populate scores from execution results
        for r in results:
            if r.validator in scores:
                scores[r.validator] = r.score
                
        # Handle Documentation Score calculation specifically
        if not has_docs:
            scores["Documentation Checker"] = 0.0
            
        # If there are no Frontend or Database files, we can default them to 100.0 (already done)
        weighted_sum = 0.0
        total_weight = 0.0
        
        for validator, weight in self.weights.items():
            weighted_sum += scores[validator] * weight
            total_weight += weight
            
        overall_score = round(weighted_sum / total_weight, 1)
        
        # Grade mapping
        if overall_score >= 98.0:
            grade = "A+"
        elif overall_score >= 95.0:
            grade = "A"
        elif overall_score >= 90.0:
            grade = "B+"
        elif overall_score >= 80.0:
            grade = "B"
        else:
            grade = "FAIL"
            
        ready_for_export = (grade != "FAIL" and overall_score >= 80.0)
        
        _logger.info(f"Quality Score Computed: {overall_score} ({grade}), Ready={ready_for_export}")
        return QualityScore(
            overall_score=overall_score,
            grade=grade,
            ready_for_export=ready_for_export
        )
