"""
AIForge Code Extractor
======================
Extracts structured CodeArtifacts from markdown response code fences.
"""

import re
from typing import List
from backend.execution.models import CodeArtifact


class CodeExtractor:
    """
    Extracts code blocks from response text into structured CodeArtifacts.
    """

    def extract_artifacts(self, response_text: str, default_language: str = "python") -> List[CodeArtifact]:
        if not response_text:
            return []

        pattern = r"```([a-zA-Z0-9_+#-]*)\n(.*?)```"
        matches = re.findall(pattern, response_text, re.DOTALL)

        artifacts: List[CodeArtifact] = []

        if not matches:
            # Check if raw code without fences
            if "def " in response_text or "function " in response_text or "class " in response_text:
                artifacts.append(
                    CodeArtifact(
                        filename="main.py" if default_language == "python" else "index.js",
                        language=default_language,
                        content=response_text.strip(),
                        purpose="SOURCE"
                    )
                )
            return artifacts

        for idx, (lang_tag, code_content) in enumerate(matches):
            lang = lang_tag.strip().lower() or default_language
            if lang in ["py"]:
                lang = "python"
            elif lang in ["js", "jsx"]:
                lang = "javascript"

            fname = f"main_{idx + 1}.py" if lang == "python" else f"index_{idx + 1}.js"
            if lang == "java":
                # Extract public class name if available
                class_match = re.search(r"public\s+class\s+([A-Za-z0-9_]+)", code_content)
                fname = f"{class_match.group(1)}.java" if class_match else "Solution.java"

            purpose = "SOURCE"
            if "def test_" in code_content or "assert " in code_content or "unittest" in code_content:
                purpose = "TEST"

            artifacts.append(
                CodeArtifact(
                    filename=fname,
                    language=lang,
                    content=code_content.strip(),
                    purpose=purpose
                )
            )

        return artifacts


global_code_extractor = CodeExtractor()
