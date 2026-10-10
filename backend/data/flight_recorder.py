"""
AIForge Data compatibility shim for FlightRecorder.
Re-exports global_flight_recorder and FlightRecorderStore from backend.autopilot.recorder.
"""
from backend.autopilot.recorder import global_flight_recorder, FlightRecorderStore

__all__ = ["global_flight_recorder", "FlightRecorderStore"]
