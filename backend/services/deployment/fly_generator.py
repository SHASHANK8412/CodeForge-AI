import logging

_logger = logging.getLogger("aiforge.performance")

class FlyGenerator:
    """
    Generates fly.toml configuration for containerized cloud deployment on Fly.io,
    specifying target ports, regional defaults, process setups, and persistent mounts.
    """

    def __init__(self) -> None:
        pass

    def generate_config(self, app_name: str, port: int = 8000) -> str:
        """
        Creates fly.toml layout.
        """
        _logger.info(f"Generating fly.toml configuration for: {app_name} on port: {port}")
        
        return f"""# Fly.io Deployment Configuration
app = "{app_name}"
primary_region = "bos"

[http_service]
  internal_port = {port}
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
  processes = ["app"]

[[services]]
  protocol = "tcp"
  internal_port = {port}
  processes = ["app"]

  [[services.ports]]
    port = 80
    handlers = ["http"]

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

  [services.concurrency]
    type = "connections"
    hard_limit = 25
    soft_limit = 20

  [[services.tcp_checks]]
    interval = "15s"
    timeout = "2s"
    grace_period = "1s"
"""
