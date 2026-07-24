"""
AIForge Day 94 Duplication Detector Module
==========================================
Detects duplicate code blocks and duplicated logic within files or across multiple files.
"""

import logging
from typing import Dict, Any, List, Optional
from backend.analysis.duplicates import DuplicateDetector

_logger = logging.getLogger("aiforge.analysis.duplication")


class CodeDuplicationDetector:
    """
    Code Duplication Detector.
    """

    def __init__(self) -> None:
        self._legacy_detector = DuplicateDetector()

    def analyze_duplication_in_code(self, code_content: str, filename: str = "main.py") -> Dict[str, Any]:
        _logger.info(f"CodeDuplicationDetector: Analyzing code duplication for '{filename}'...")

        lines = [line.strip() for line in code_content.splitlines() if line.strip() and not line.strip().startswith("#")]
        seen_chunks = {}
        duplicate_blocks = []

        chunk_size = 3
        for i in range(len(lines) - chunk_size + 1):
            chunk = "\n".join(lines[i:i+chunk_size])
            if chunk in seen_chunks:
                duplicate_blocks.append({
                    "lines": f"{i+1}-{i+chunk_size}",
                    "first_seen": seen_chunks[chunk],
                    "content": chunk[:60] + "..."
                })
            else:
                seen_chunks[chunk] = i + 1

        duplication_pct = round((len(duplicate_blocks) * chunk_size / max(1, len(lines))) * 100, 1)

        return {
            "filename": filename,
            "duplicate_blocks_count": len(duplicate_blocks),
            "duplication_percentage": min(100.0, duplication_pct),
            "duplicate_blocks": duplicate_blocks
        }

    def analyze_duplicates(self, file_metadata: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self._legacy_detector.analyze_duplicates(file_metadata)


global_duplication_detector = CodeDuplicationDetector()
