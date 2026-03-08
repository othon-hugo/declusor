from dataclasses import dataclass
from threading import Event, Thread
from typing import Any, Callable, Generator, Iterator, Literal, Self

TaskHandler = Callable[["TaskEvent"], Any]


class TaskEvent(Event):
    """A ``threading.Event`` used as a cooperative stop-flag for ``TaskPool`` tasks."""


@dataclass
class Task:
    """Holds the outcome of a single task execution (result or exception)."""

    result: Any | None = None
    exception: Exception | None = None


class TaskPool:
    """Manages a bounded pool of daemon threads with cooperative cancellation.

    Tasks are registered via ``add_task``, started with ``start_all``, and
    cancelled by setting the shared ``TaskEvent`` (via ``stop``). Results and
    exceptions are collected in ``Task`` objects accessible through ``errors``
    and ``return_all``.

    Supports the context manager protocol: starts all tasks on enter, drains
    and raises any exceptions on exit.
    """

    def __init__(self, stop_event: TaskEvent | None = None, max_size: int = 10, daemon_mode: bool = True):
        self._daemon_mode = daemon_mode
        self._max_size = max_size
        self._stop_event = stop_event or TaskEvent()

        self._threads: dict[Thread, Task] = {}
        self._results: list[Task] = []

    @property
    def errors(self) -> list[Exception]:
        """Return exceptions from all completed tasks."""

        return [r.exception for r in self._results if r.exception is not None]

    def add_task(self, handle_task: TaskHandler, /, name: str | None = None) -> None:
        """Register a task without starting it.

        Args:
            handle_task: Callable that accepts a ``TaskEvent`` stop-flag.
            name: Optional name for the underlying thread (aids debugging).

        Raises:
            RuntimeError: If the pool is already at ``max_size`` threads.
        """

        if len(self._threads) >= self._max_size:
            raise RuntimeError("Maximum number of threads reached")

        thread_task = Task()
        thread = Thread(target=self._run_task, args=(handle_task, thread_task), daemon=self._daemon_mode, name=name)

        self._threads[thread] = thread_task

    def start_all(self) -> None:
        """Start all registered threads."""

        self._stop_event.clear()

        for thread in self._threads:
            if not thread.is_alive():
                thread.start()

    def wait_all(self) -> None:
        """Wait until all threads have finished execution."""

        for thread in list(self._threads):
            thread.join()

    def stop(self) -> None:
        """Signal all threads to stop (cooperative cancellation)."""

        self._stop_event.set()

    def return_all(self, timeout: float = 5.0, /) -> Generator[Task, None, None]:
        """Stop all threads, join them, and yield their ``Task`` results one by one.

        Sets the stop-event, waits up to *timeout* seconds per thread, and
        records a ``TimeoutError`` for any thread that does not exit in time.

        Args:
            timeout: Seconds to wait for each thread to finish. Defaults to 5.

        Yields:
            One ``Task`` per registered thread, in registration order.
        """

        self._stop_event.set()

        for thread, task in tuple(self._threads.items()):
            thread.join(timeout=timeout)

            if thread.is_alive():
                task.exception = TimeoutError(f"Thread {thread.name or thread.native_id!r} did not exit in time")

            self._threads.pop(thread)
            yield task

            self._results.append(task)

    def _run_task(self, handle_task: TaskHandler, /, thread_result: Task) -> None:
        try:
            thread_result.result = handle_task(self._stop_event)
        except Exception as e:
            thread_result.exception = e

    def __enter__(self) -> Self:
        self.start_all()

        return self

    def __exit__(self, exc_t: type[BaseException] | None, exc_v: BaseException | None, exc_tb: Exception | None) -> Literal[False]:
        for _ in self.return_all():
            pass

        if errors := self.errors:
            raise ExceptionGroup("One or more exceptions occurred during thread execution.", errors) from exc_tb

        return False

    def __iter__(self) -> Iterator[Task]:
        """Iterate over remaining tasks."""

        return iter(tuple(self._threads.values()))
