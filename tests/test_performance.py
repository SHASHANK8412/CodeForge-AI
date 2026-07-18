import time
from backend.utils.timer import Timer
from backend.graph.profiler import Profiler


def test_timer_context_manager():
    with Timer() as timer:
        time.sleep(0.05)
    assert timer.elapsed >= 0.04


def test_profiler_reports():
    profiler = Profiler()

    profiler.record_agent_time("planner", 1.2)
    profiler.record_agent_time("architect", 2.0)
    profiler.record_agent_time("frontend", 4.5)
    profiler.set_total_time(10.5)

    assert profiler.get_agent_time("planner") == 1.2
    assert profiler.get_agent_time("architect") == 2.0
    assert profiler.get_agent_time("frontend") == 4.5
    assert profiler.get_total_time() == 10.5

    avg = profiler.get_average_agent_time()
    assert abs(avg - (1.2 + 2.0 + 4.5) / 3) < 0.01

    slowest_name, slowest_time = profiler.get_slowest_agent()
    assert slowest_name == "Frontend"
    assert slowest_time == 4.5

    report = profiler.format_report()
    assert "Planner" in report
    assert "1.2 s" in report
    assert "Total" in report
    assert "10.5 s" in report
