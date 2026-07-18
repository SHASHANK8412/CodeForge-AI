from threading import Lock


class Profiler:
    """
    A thread-safe profiler to record execution times for agent nodes and
    calculate workflow performance metrics.
    """

    def __init__(self) -> None:
        self._times: dict[str, float] = {}
        self._lock = Lock()
        self._total_time: float = 0.0

    def record_agent_time(self, agent_name: str, duration: float) -> None:
        """
        Record the execution time (in seconds) for a specific agent.
        """
        with self._lock:
            self._times[agent_name.lower()] = duration

    def set_total_time(self, duration: float) -> None:
        """
        Record the total workflow execution time (in seconds).
        """
        with self._lock:
            self._total_time = duration

    def get_agent_time(self, agent_name: str) -> float:
        """
        Get the execution time (in seconds) for a specific agent.
        """
        with self._lock:
            return self._times.get(agent_name.lower(), 0.0)

    def get_all_times(self) -> dict[str, float]:
        """
        Get a copy of all recorded agent times.
        """
        with self._lock:
            return dict(self._times)

    def get_total_time(self) -> float:
        """
        Get the total workflow execution time.
        """
        with self._lock:
            return self._total_time

    def get_average_agent_time(self) -> float:
        """
        Calculate the average execution time across all recorded agents.
        """
        with self._lock:
            if not self._times:
                return 0.0
            return sum(self._times.values()) / len(self._times)

    def get_slowest_agent(self) -> tuple[str, float]:
        """
        Find the slowest agent and its execution time.
        Returns a tuple of (agent_name, duration).
        """
        with self._lock:
            if not self._times:
                return ("", 0.0)
            slowest = max(self._times.items(), key=lambda item: item[1])
            return slowest[0].capitalize(), slowest[1]

    def clear(self) -> None:
        """
        Clear all recorded metrics.
        """
        with self._lock:
            self._times.clear()
            self._total_time = 0.0

    def format_report(self) -> str:
        """
        Generates the standard Day 20 performance report text.
        """
        with self._lock:
            lines = []
            for agent in ["planner", "architect", "frontend", "backend", "database", "testing", "documentation", "reviewer"]:
                name = agent.capitalize()
                duration = self._times.get(agent, 0.0)
                dots = "." * (20 - len(name))
                lines.append(f"{name} {dots} {duration:.1f} s")
            total_dots = "." * (20 - len("Total"))
            lines.append(f"Total {total_dots} {self._total_time:.1f} s")
            return "\n".join(lines)


# Singleton instance for easy workflow profiling integration
workflow_profiler = Profiler()
