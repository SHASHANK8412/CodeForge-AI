"""
AIForge Port Manager Module
===========================
Dynamically detects available TCP ports, prevents port collisions across services,
assigns frontend and backend ports, tracks running bindings, and releases ports upon shutdown.
"""

import socket
import logging
from typing import Dict, Any, Optional, Set
from threading import Lock
from pydantic import BaseModel, Field

_logger = logging.getLogger("aiforge.execution.port_manager")


class ServicePortBinding(BaseModel):
    service_name: str
    port: int
    host: str = "127.0.0.1"
    url: str


class PortManager:
    """
    Thread-safe port allocator and process binding tracker.
    """

    def __init__(self, start_port: int = 5000, end_port: int = 9000):
        self.start_port = start_port
        self.end_port = end_port
        self._lock = Lock()
        self._allocated_ports: Dict[str, ServicePortBinding] = {}
        self._reserved_ports: Set[int] = set()

    def is_port_available(self, port: int, host: str = "127.0.0.1") -> bool:
        """Checks if a TCP port is currently free and unassigned."""
        with self._lock:
            if port in self._reserved_ports:
                return False

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((host, port))
                return True
        except OSError:
            return False

    def find_free_port(self, preferred_port: Optional[int] = None, host: str = "127.0.0.1") -> int:
        """Finds an available TCP port near preferred_port or in range."""
        if preferred_port and self.is_port_available(preferred_port, host):
            return preferred_port

        for port in range(self.start_port, self.end_port):
            if self.is_port_available(port, host):
                return port

        raise RuntimeError(f"No available TCP ports found in range {self.start_port}-{self.end_port}")

    def allocate_ports_for_fullstack(
        self,
        project_id: str,
        preferred_fe_port: int = 5173,
        preferred_be_port: int = 8000
    ) -> Dict[str, ServicePortBinding]:
        """Allocates distinct ports for frontend and backend services."""
        with self._lock:
            fe_port = self.find_free_port(preferred_fe_port)
            self._reserved_ports.add(fe_port)

            be_port = self.find_free_port(preferred_be_port if preferred_be_port != fe_port else preferred_be_port + 1)
            self._reserved_ports.add(be_port)

            fe_binding = ServicePortBinding(
                service_name="frontend",
                port=fe_port,
                host="127.0.0.1",
                url=f"http://localhost:{fe_port}"
            )
            be_binding = ServicePortBinding(
                service_name="backend",
                port=be_port,
                host="127.0.0.1",
                url=f"http://localhost:{be_port}"
            )

            self._allocated_ports[f"{project_id}:frontend"] = fe_binding
            self._allocated_ports[f"{project_id}:backend"] = be_binding

            _logger.info(f"PortManager: Allocated {project_id} -> Frontend: {fe_binding.url}, Backend: {be_binding.url}")
            return {
                "frontend": fe_binding,
                "backend": be_binding
            }

    def release_ports_for_project(self, project_id: str) -> None:
        """Releases allocated ports for a project."""
        with self._lock:
            keys_to_remove = [k for k in self._allocated_ports if k.startswith(f"{project_id}:")]
            for k in keys_to_remove:
                binding = self._allocated_ports.pop(k, None)
                if binding and binding.port in self._reserved_ports:
                    self._reserved_ports.remove(binding.port)
                    _logger.info(f"PortManager: Released port {binding.port} for {k}")

    def get_binding(self, project_id: str, service_name: str) -> Optional[ServicePortBinding]:
        with self._lock:
            return self._allocated_ports.get(f"{project_id}:{service_name}")


global_port_manager = PortManager()
