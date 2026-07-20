import asyncio
import logging
from typing import Optional
from backend.monitoring.config import sre_settings
from backend.monitoring.monitor import OpsMonitor

_logger = logging.getLogger("aiforge.sre")

class OpsScheduler:
    """
    Manages the asynchronous background loop for continuous monitoring,
    failure forecasting, and self-healing execution.
    """

    def __init__(self, monitor: OpsMonitor) -> None:
        self.monitor = monitor
        self.task: Optional[asyncio.Task] = None
        self.running = False

    def start(self) -> None:
        """
        Spawns the SRE background scheduling loop task.
        """
        if self.running:
            _logger.warning("SRE background task scheduler is already running.")
            return

        self.running = True
        self.task = asyncio.create_task(self._run_loop())
        _logger.info("SRE background task scheduler started successfully.")

    def stop(self) -> None:
        """
        Stops the SRE background scheduling loop task.
        """
        if not self.running:
            return

        self.running = False
        if self.task:
            self.task.cancel()
            self.task = None
        _logger.info("SRE background task scheduler stopped.")

    async def _run_loop(self) -> None:
        """
        Continuous polling loop.
        """
        while self.running:
            try:
                # Execute SRE loop step
                outcome = await self.monitor.execute_operations_step()
                _logger.info(f"SRE loop step completed. Health score: {outcome.get('health_score')}/100")
                
                # Sleep for configured interval
                await asyncio.sleep(sre_settings.polling_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                _logger.error(f"Error executing SRE polling step: {str(e)}")
                await asyncio.sleep(sre_settings.polling_interval)
