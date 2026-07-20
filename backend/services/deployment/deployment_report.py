from dataclasses import dataclass, field
from typing import Dict, List, Any

@dataclass
class DeploymentReadinessReport:
    """
    Represents the detailed deployment readiness validation diagnostics report.
    """
    ready: bool = False
    readiness_score: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    detected_frameworks: Dict[str, str] = field(default_factory=dict)
    detected_databases: List[str] = field(default_factory=list)
    suggested_platform: str = "Unknown"
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ready": self.ready,
            "readiness_score": self.readiness_score,
            "errors": self.errors,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "detected_frameworks": self.detected_frameworks,
            "detected_databases": self.detected_databases,
            "suggested_platform": self.suggested_platform,
            "reasoning": self.reasoning,
        }
