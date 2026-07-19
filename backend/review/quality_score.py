import logging

_logger = logging.getLogger("aiforge.performance")


class QualityScoreCalculator:
    """
    Computes diagnostic quality scores (out of 10.0) based on findings from
    reviewer, security, architecture, performance checkers, and test execution results.
    """

    def __init__(self) -> None:
        pass

    def calculate_scores(self, findings: list[dict], test_results: dict) -> dict:
        """
        Calculates sub-scores and overall project score.
        """
        _logger.info("Calculating quality scores...")

        # Base scores start at 10.0
        arch_score = 10.0
        sec_score = 10.0
        perf_score = 10.0
        maint_score = 10.0
        test_score = 10.0
        doc_score = 10.0

        # 1. Deduct for Architecture issues
        for finding in findings:
            issue_lower = finding.get("issue", "").lower()
            rec_lower = finding.get("recommendation", "").lower()
            
            # Identify architecture checks
            if any(term in issue_lower or term in rec_lower for term in ["circular", "naming", "unused import", "duplicate module", "structure"]):
                # Deduct based on severity
                sev = finding.get("severity", "info").lower()
                if sev == "critical":
                    arch_score -= 2.0
                elif sev == "warning":
                    arch_score -= 1.0
                else:
                    arch_score -= 0.5

        # 2. Deduct for Security issues
        for finding in findings:
            issue_lower = finding.get("issue", "").lower()
            rec_lower = finding.get("recommendation", "").lower()

            if any(term in issue_lower or term in rec_lower for term in ["sql injection", "secret", "token", "password", "shell=true", "deserialization", "hashing", "sanitize"]):
                sev = finding.get("severity", "info").lower()
                if sev == "critical":
                    sec_score -= 2.5
                elif sev == "warning":
                    sec_score -= 1.5
                else:
                    sec_score -= 0.5

        # 3. Deduct for Performance issues
        for finding in findings:
            issue_lower = finding.get("issue", "").lower()
            rec_lower = finding.get("recommendation", "").lower()

            if any(term in issue_lower or term in rec_lower for term in ["loop", "sleep", "blocking", "cache", "efficiency", "algorithm"]):
                sev = finding.get("severity", "info").lower()
                if sev == "critical":
                    perf_score -= 2.0
                elif sev == "warning":
                    perf_score -= 1.0
                else:
                    perf_score -= 0.5

        # 4. Deduct for Readability/Maintainability based on LLM reviewer warnings
        for finding in findings:
            sev = finding.get("severity", "info").lower()
            if sev == "critical":
                maint_score -= 1.5
            elif sev == "warning":
                maint_score -= 0.8
            else:
                maint_score -= 0.3

        # 5. Deduct for Documentation missing
        for finding in findings:
            issue_lower = finding.get("issue", "").lower()
            if "docstring" in issue_lower or "documentation" in issue_lower:
                doc_score -= 1.0

        # 6. Deduct for failing tests
        total_failed = test_results.get("failed", 0) + test_results.get("errors", 0)
        total_passed = test_results.get("passed", 0)
        
        if total_failed > 0:
            test_score -= (total_failed * 2.0)
        elif total_passed == 0:
            test_score = 5.0 # No tests run but none failed

        # Ensure scores are within bounds [0.0, 10.0]
        scores = {
            "architecture": max(0.0, min(10.0, round(arch_score, 1))),
            "security": max(0.0, min(10.0, round(sec_score, 1))),
            "performance": max(0.0, min(10.0, round(perf_score, 1))),
            "maintainability": max(0.0, min(10.0, round(maint_score, 1))),
            "testing": max(0.0, min(10.0, round(test_score, 1))),
            "documentation": max(0.0, min(10.0, round(doc_score, 1))),
        }

        # Calculate Overall score
        overall = sum(scores.values()) / len(scores)
        scores["overall"] = round(overall, 1)

        _logger.info(f"Quality scores computed: {scores}")
        return scores
