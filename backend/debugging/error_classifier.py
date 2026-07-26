import logging
from typing import Dict, Any, List

logger = logging.getLogger("aiforge.debugging.error_classifier")


class ErrorClassifier:
    """
    ErrorClassifier categorizes runtime exceptions (Syntax, Import, Runtime, DB, API, Docker, Dependency),
    assigns severity ratings, root cause descriptions, and suggested fix strategies.
    """

    ERROR_PATTERNS = {
        "ModuleNotFoundError": ("Import", "HIGH", "Missing dependency package in requirements.txt."),
        "ImportError": ("Import", "HIGH", "Broken import reference or missing module path."),
        "SyntaxError": ("Syntax", "HIGH", "Syntax error in Python or React JSX component."),
        "AttributeError": ("Runtime", "MEDIUM", "Method or property accessed on None or undefined object."),
        "OperationalError": ("Database", "HIGH", "Database connection or schema table missing error."),
        "ExportMissing": ("Frontend", "MEDIUM", "React component lacks default or named export.")
    }

    def classify_error(self, err_type: str, message: str, filepath: str = "") -> Dict[str, Any]:
        category, severity, root_cause = self.ERROR_PATTERNS.get(
            err_type,
            ("Runtime", "MEDIUM", f"Runtime exception: {message[:100]}")
        )

        suggested_fix = "Update source code or dependencies to resolve exception."
        if category == "Import":
            suggested_fix = "Automatically append missing module to requirements.txt and re-install."
        elif category == "Syntax":
            suggested_fix = "Fix syntax error or missing closing tag."
        elif category == "Frontend":
            suggested_fix = "Add default export statement to React component file."

        return {
            "error_type": err_type,
            "category": category,
            "severity": severity,
            "filepath": filepath,
            "root_cause": root_cause,
            "suggested_fix": suggested_fix,
            "raw_message": message
        }


# Global ErrorClassifier Instance
global_error_classifier = ErrorClassifier()
