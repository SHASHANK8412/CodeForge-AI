from time import perf_counter
from types import TracebackType
from typing import Self


class Timer:
    """
    A context manager to measure elapsed execution time in seconds.
    """

    def __init__(self) -> None:
        self.start_time: float | None = None
        self.elapsed: float = 0.0

    def __enter__(self) -> Self:
        self.start_time = perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self.start_time is not None:
            self.elapsed = perf_counter() - self.start_time
