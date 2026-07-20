import time
import logging
from typing import Dict, Any, List

_logger = logging.getLogger("aiforge.sre")

class FailurePredictor:
    """
    Applies mathematical extrapolation (slope analysis) over historical telemetry logs
    to predict resource depletion (CPU, Memory, Disk) and traffic anomalies.
    """

    def __init__(self, prediction_window_seconds: float = 60.0) -> None:
        self.prediction_window = prediction_window_seconds

    def predict_failures(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Scans historical metrics, extrapolates slopes, and compiles predictive warnings.
        """
        predictions: List[Dict[str, Any]] = []
        if len(history) < 5:
            # Insufficient data to fit a slope
            return predictions

        timestamp_now = time.time()

        # Extract values and timestamps
        timestamps = [item["timestamp"] for item in history]
        cpu_values = [item["infrastructure"]["cpu_utilization"] for item in history]
        mem_values = [item["infrastructure"]["memory_utilization"] for item in history]
        disk_values = [item["infrastructure"]["disk_utilization"] for item in history]
        queue_values = [item["application"].get("queue_depth", 0) for item in history]

        # Calculate slopes (least-squares simple linear regression)
        cpu_slope = self._calculate_slope(timestamps, cpu_values)
        mem_slope = self._calculate_slope(timestamps, mem_values)
        disk_slope = self._calculate_slope(timestamps, disk_values)
        queue_slope = self._calculate_slope(timestamps, queue_values)

        # 1. Forecast Memory exhaustion
        latest_mem = mem_values[-1]
        predicted_mem = latest_mem + (mem_slope * self.prediction_window)
        if predicted_mem >= 95.0:
            predictions.append({
                "metric": "Memory Usage",
                "current_value": latest_mem,
                "predicted_value": min(100.0, predicted_mem),
                "time_to_threshold_seconds": self._time_to_threshold(95.0, latest_mem, mem_slope),
                "severity": "Critical",
                "recommendation": "Perform heap dump investigation / Scale replicas horizontally to distribute memory load."
            })
            _logger.warning(f"[PREDICTIVE ALERT] High probability of memory exhaustion in < {self.prediction_window}s!")

        # 2. Forecast CPU saturation
        latest_cpu = cpu_values[-1]
        predicted_cpu = latest_cpu + (cpu_slope * self.prediction_window)
        if predicted_cpu >= 95.0:
            predictions.append({
                "metric": "CPU Saturation",
                "current_value": latest_cpu,
                "predicted_value": min(100.0, predicted_cpu),
                "time_to_threshold_seconds": self._time_to_threshold(95.0, latest_cpu, cpu_slope),
                "severity": "Warning",
                "recommendation": "Configure automatic container horizontal scaling threshold adjustment."
            })

        # 3. Forecast Disk exhaustion
        latest_disk = disk_values[-1]
        predicted_disk = latest_disk + (disk_slope * self.prediction_window)
        if predicted_disk >= 98.0:
            predictions.append({
                "metric": "Disk Capacity",
                "current_value": latest_disk,
                "predicted_value": min(100.0, predicted_disk),
                "time_to_threshold_seconds": self._time_to_threshold(98.0, latest_disk, disk_slope),
                "severity": "Critical",
                "recommendation": "Run automated logs logrotate purge scripts to prevent system lockups."
            })

        # 4. Forecast Queue saturation
        latest_queue = queue_values[-1]
        predicted_queue = latest_queue + (queue_slope * self.prediction_window)
        if predicted_queue >= 80:
            predictions.append({
                "metric": "Queue Depth",
                "current_value": latest_queue,
                "predicted_value": predicted_queue,
                "time_to_threshold_seconds": self._time_to_threshold(80, latest_queue, queue_slope),
                "severity": "Warning",
                "recommendation": "Spawn supplementary queue background worker processes."
            })

        return predictions

    def _calculate_slope(self, x: List[float], y: List[float]) -> float:
        """
        Calculates the linear regression slope.
        """
        n = len(x)
        if n == 0:
            return 0.0
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_xx = sum(xi * xi for xi in x)

        denom = (n * sum_xx - sum_x * sum_x)
        if abs(denom) < 1e-6:
            return 0.0
        return (n * sum_xy - sum_x * sum_y) / denom

    def _time_to_threshold(self, threshold: float, current: float, slope: float) -> float:
        if slope <= 1e-6:
            return 9999.0
        diff = threshold - current
        if diff <= 0:
            return 0.0
        return diff / slope
