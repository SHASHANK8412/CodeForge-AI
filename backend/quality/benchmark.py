import time
import logging
from typing import Dict, Any

logger = logging.getLogger("aiforge.quality.benchmark")


class QualityBenchmarker:
    """
    QualityBenchmarker measures performance metrics (generation time, assembly time,
    validation time, optimization time, total export time).
    """

    def benchmark_pipeline(self, project_id: str, stage_timings: Dict[str, float]) -> Dict[str, Any]:
        total_time = sum(stage_timings.values())
        return {
            "project_id": project_id,
            "total_time_seconds": round(total_time, 3),
            "stage_timings_seconds": stage_timings,
            "timestamp": time.time()
        }


# Global QualityBenchmarker Instance
global_quality_benchmarker = QualityBenchmarker()
