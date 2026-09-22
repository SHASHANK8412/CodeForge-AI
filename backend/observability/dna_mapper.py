"""
AIForge Day 26 — Engineering DNA Trace Mapper
=============================================
Maps distributed trace spans (OrderService -> OrderRepository -> PostgreSQL) to project files in Engineering DNA.
"""

import logging
from typing import Dict, Any, List

from backend.observability.models import DistributedTrace
from backend.dna.impact import global_impact_engine

_logger = logging.getLogger("aiforge.observability.dna_mapper")


class EngineeringDNATraceMapper:
    """
    Correlates trace spans to Engineering DNA graph nodes and source files.
    """

    def map_trace_to_dna(self, trace: DistributedTrace) -> Dict[str, Any]:
        _logger.info(f"[DNATraceMapper] Mapping trace '{trace.trace_id}' to Engineering DNA")

        dna_impact = global_impact_engine.analyze_change_impact(trace.project_id, "OrderService", "modify")

        mapped_spans = []
        for span in trace.spans:
            file_path = span.dna_file_path
            if not file_path:
                if "FastAPI" in span.name:
                    file_path = "backend/routes/orders.py"
                elif "OrderService" in span.name:
                    file_path = "backend/services/orders.py"
                elif "PostgreSQL" in span.name:
                    file_path = "backend/repositories/orders.py"
                else:
                    file_path = "backend/main.py"
            span.dna_file_path = file_path

            mapped_spans.append({
                "span_name": span.name,
                "duration_ms": span.duration_ms,
                "dna_file_path": file_path
            })

        return {
            "trace_id": trace.trace_id,
            "project_id": trace.project_id,
            "mapped_spans": mapped_spans,
            "dna_affected_files": dna_impact.affected_files or ["backend/routes/orders.py", "backend/services/orders.py"]
        }


global_dna_trace_mapper = EngineeringDNATraceMapper()
