import time

import pytest

from declusor.util import concurrency


def test_task_pool_execution_and_results() -> None:
    """Verify tasks execute and results are collected."""
    pool = concurrency.TaskPool()

    def task_fn(stop_event: concurrency.TaskEvent) -> int:
        return 42

    pool.add_task(task_fn, name="worker-1")
    pool.start_all()
    pool.wait_all()

    tasks = list(pool.return_all())
    assert len(tasks) == 1
    assert tasks[0].result == 42
    assert tasks[0].exception is None


def test_task_pool_exception_capture() -> None:
    """Verify task exceptions are captured in errors property."""
    pool = concurrency.TaskPool()

    def failing_task(stop_event: concurrency.TaskEvent) -> None:
        raise ValueError("task failure")

    pool.add_task(failing_task, name="failing-worker")
    pool.start_all()
    pool.wait_all()

    list(pool.return_all())
    assert len(pool.errors) == 1
    assert isinstance(pool.errors[0], ValueError)


def test_task_pool_max_size_limit() -> None:
    """Verify TaskPool enforces max_size limit."""
    pool = concurrency.TaskPool(max_size=1)

    pool.add_task(lambda _: None)
    with pytest.raises(RuntimeError, match="Maximum number of threads reached"):
        pool.add_task(lambda _: None)


def test_task_pool_cooperative_stop() -> None:
    """Verify stop signals the TaskEvent."""
    event = concurrency.TaskEvent()
    pool = concurrency.TaskPool(stop_event=event)

    executed = False

    def stoppable_task(stop_event: concurrency.TaskEvent) -> None:
        nonlocal executed
        while not stop_event.is_set():
            time.sleep(0.01)
        executed = True

    pool.add_task(stoppable_task)
    pool.start_all()
    pool.stop()
    pool.wait_all()

    assert executed is True
