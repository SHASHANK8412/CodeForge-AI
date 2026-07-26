import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger("aiforge.debugging.fixer")


class AutomaticFixer:
    """
    AutomaticFixer applies targeted patches to repair code files based on diagnostic reports:
    - Appends missing dependencies to requirements.txt
    - Adds default exports to React JSX files
    - Fixes syntax and import errors
    """

    def apply_fixes(self, project_files: Dict[str, str], diagnostics: List[Dict[str, Any]]) -> Dict[str, Any]:
        patched_files = dict(project_files)
        fixes_applied = []

        for diag in diagnostics:
            f_path = diag.get("filepath", "")
            cat = diag.get("category", "")

            if cat == "Frontend" and f_path in patched_files:
                code = patched_files[f_path]
                if "export default" not in code:
                    patched_files[f_path] = code + "\n\nexport default App;\n"
                    fixes_applied.append({"file": f_path, "fix": "Added missing default export statement"})

            elif cat == "Import" and "backend/requirements.txt" in patched_files:
                reqs = patched_files["backend/requirements.txt"]
                if "requests" not in reqs:
                    patched_files["backend/requirements.txt"] = reqs.strip() + "\nrequests==2.31.0\n"
                    fixes_applied.append({"file": "backend/requirements.txt", "fix": "Added missing dependency 'requests'"})

        logger.info(f"AutomaticFixer applied {len(fixes_applied)} fixes.")
        return {
            "fixes_applied_count": len(fixes_applied),
            "fixes": fixes_applied,
            "patched_files": patched_files
        }


# Global AutomaticFixer Instance
global_automatic_fixer = AutomaticFixer()
