import logging
from typing import Dict, List, Set

_logger = logging.getLogger("aiforge.project_intelligence")

class ImpactAnalyzer:
    """
    Computes recursive transitives upstream dependencies to forecast impact checklists.
    """

    def __init__(self) -> None:
        pass

    def analyze_impact(self, dep_graph: Dict[str, List[str]], target_file: str) -> List[str]:
        """
        Calculates all upstream modules referencing or importing target_file.
        """
        impacted: Set[str] = set()
        
        # Build inverted lookup (who imports key?)
        inverted: Dict[str, Set[str]] = {}
        for parent, children in dep_graph.items():
            for child in children:
                # Approximate resolution matching relative strings
                inverted.setdefault(child, set()).add(parent)

        def traverse(node: str) -> None:
            # Look for exact or relative path matches
            for k in inverted:
                if node in k or k in node:
                    for parent in inverted[k]:
                        if parent not in impacted:
                            impacted.add(parent)
                            traverse(parent)

        traverse(target_file)
        
        return list(impacted)
