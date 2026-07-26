import hashlib
import logging
from typing import Dict, Any, List

logger = logging.getLogger("aiforge.quality.duplicate_detector")


class DuplicateDetector:
    """
    DuplicateDetector finds duplicated functions, blocks of code, or components
    across project files and recommends refactoring.
    """

    def detect_duplicates(self, project_files: Dict[str, str]) -> Dict[str, Any]:
        block_hashes: Dict[str, List[str]] = {}

        chunk_size = 3
        for filepath, content in project_files.items():
            lines = [line.strip() for line in content.split("\n") if line.strip() and not line.strip().startswith("#")]
            if len(lines) >= chunk_size:
                for i in range(len(lines) - chunk_size + 1):
                    chunk = "\n".join(lines[i:i+chunk_size])
                    h = hashlib.md5(chunk.encode("utf-8")).hexdigest()
                    block_hashes.setdefault(h, []).append(filepath)

        duplicates = []
        for h, files in block_hashes.items():
            unique_files = list(set(files))
            if len(unique_files) > 1:
                duplicates.append({
                    "files": unique_files,
                    "type": "CodeDuplication",
                    "recommendation": "Extract duplicated code logic into a shared helper module."
                })

        return {
            "duplicate_count": len(duplicates),
            "duplicates": duplicates
        }


# Global DuplicateDetector Instance
global_duplicate_detector = DuplicateDetector()
