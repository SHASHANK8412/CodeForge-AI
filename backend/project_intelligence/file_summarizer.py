import re
import logging
from pathlib import Path
from typing import Dict, Any

_logger = logging.getLogger("aiforge.project_intelligence")

class FileSummarizer:
    """
    Statically analyzes code definitions to generate file summaries.
    """

    def __init__(self) -> None:
        self.class_pattern = re.compile(r'class\s+([a-zA-Z0-9_]+)')
        self.func_pattern = re.compile(r'(?:def|function)\s+([a-zA-Z0-9_]+)')

    def generate_summary(self, file_path: Path) -> Dict[str, Any]:
        """
        Parses functions, classes, and comments inside code file.
        """
        classes = []
        functions = []
        docstring = ""

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Find classes & functions
            classes = self.class_pattern.findall(content)
            functions = self.func_pattern.findall(content)

            # Look for docstring comment block
            doc_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
            if doc_match:
                docstring = doc_match.group(1).strip()
            else:
                docstring = f"Code file exporting {len(functions)} functions and {len(classes)} classes."

        except Exception as e:
            _logger.error(f"Failed to summarize file {file_path.name}: {str(e)}")

        return {
            "filename": file_path.name,
            "classes_declared": classes,
            "functions_declared": functions,
            "docstring_summary": docstring
        }
