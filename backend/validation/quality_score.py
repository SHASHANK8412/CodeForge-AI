import logging
from typing import List, Dict, Optional, Any

from backend.validation.models import QualityScore, ValidationResult

_logger = logging.getLogger("aiforge.performance")

class QualityScoreCalculator:
    """
    Computes weighted quality scores and grades for validated code bases.
    """

    def __init__(self) -> None:
        self.weights = {
            "Syntax Checker": 0.20,
            "Security Checker": 0.15,
            "Performance Checker": 0.10,
            "Architecture Checker": 0.15,
            "API Checker": 0.10,
            "Requirement Fidelity": 0.15,
            "Frontend Checker": 0.05,
            "Database Checker": 0.05,
            "Documentation Checker": 0.05
        }

    def compute_score(
        self,
        results: List[ValidationResult],
        has_docs: bool = True,
        requirement_fidelity: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        _logger.info("Computing final quality score...")
        
        # Build score lookup map, fallback to 100.0 if not run
        scores = {k: 100.0 for k in self.weights.keys()}
        
        # Populate scores from execution results
        for r in results:
            if r.validator in scores:
                scores[r.validator] = r.score
                
        # Populate Requirement Fidelity Score
        req_failed = False
        if requirement_fidelity:
            fidelity_score = float(requirement_fidelity.get("fidelity_score", 100.0))
            scores["Requirement Fidelity"] = fidelity_score
            if requirement_fidelity.get("status") == "FAIL" or not requirement_fidelity.get("domain_matched", True):
                req_failed = True
                
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
        
        # Grade mapping (Fails immediately if requirement fidelity fails)
        if req_failed:
            grade = "FAIL"
        elif overall_score >= 98.0:
            grade = "A+"
        elif overall_score >= 95.0:
            grade = "A"
        elif overall_score >= 90.0:
            grade = "B+"
        elif overall_score >= 80.0:
            grade = "B"
        else:
            grade = "FAIL"
            
        ready_for_export = (grade != "FAIL" and overall_score >= 80.0 and not req_failed)
        
        _logger.info(f"Quality Score Computed: {overall_score} ({grade}), Ready={ready_for_export}")
        return QualityScore(
            overall_score=overall_score,
            grade=grade,
            ready_for_export=ready_for_export
        )

