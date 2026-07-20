from pydantic import BaseModel, Field
from typing import List

class SRESettings(BaseModel):
    """
    Configurable settings for the AI-SRE monitoring and self-healing subsystem.
    """
    polling_interval: float = Field(default=5.0, description="Interval in seconds between metrics collections")
    health_check_frequency: float = Field(default=10.0, description="Interval in seconds between comprehensive health checks")
    retry_count: int = Field(default=3, description="Maximum recovery attempts for a single incident signature")
    recovery_timeout: float = Field(default=30.0, description="Maximum execution timeout in seconds for a recovery action")
    confidence_threshold: float = Field(default=0.70, description="Minimum SRE model confidence score required to auto-heal")
    prediction_window: float = Field(default=60.0, description="Forecast window in seconds for predictive analytics")
    alert_channels: List[str] = Field(default_factory=lambda: ["slack", "email"], description="Active alert notifying channels")
    
    # Scaling settings
    scaling_cpu_threshold: float = Field(default=80.0, description="CPU usage threshold to trigger scaling")
    scaling_mem_threshold: float = Field(default=85.0, description="Memory usage threshold to trigger scaling")
    scaling_queue_threshold: int = Field(default=100, description="Pending queue size threshold to trigger scaling")

# Default global settings instance
sre_settings = SRESettings()
