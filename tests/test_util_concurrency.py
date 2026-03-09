"""Tests for the ``declusor.util.concurrency`` module."""

import time
import pytest

from declusor.util import concurrency


# =============================================================================
# Tests: concurrency.TaskPool.__init__ (Initialization)
# =============================================================================

def test_taskpool_initializes_with_default_arguments() -> None:
    """``concurrency.TaskPool`` initialization must set up an empty thread pool with default configurations."""

    # ARRANGE & ACT: Initialize a new ``TaskPool`` instance
    pool = concurrency.TaskPool()

    # ASSERT: Check that the default parameters are correctly set natively
    assert pool._daemon_mode is True
    assert pool._max_size == 10
    assert isinstance(pool._stop_event, concurrency.TaskEvent)
    assert not pool._threads
    assert not pool._results


# =============================================================================
# Tests: concurrency.TaskPool.add_task (Registering tasks)
# =============================================================================

def test_add_task_under_max_size_succeeds() -> None:
    """Adding a task below the maximum pool size must register the task without starting it."""

    # ARRANGE: Create an empty pool and a dummy task function
    pool = concurrency.TaskPool()

    def dummy_task(event: concurrency.TaskEvent) -> None:
        pass

    # ACT: Add the task to the pool
    pool.add_task(dummy_task)

    # ASSERT: The task should be loaded in the internal registry but not started
    assert len(pool._threads) == 1

    thread = list(pool._threads.keys())[0]

    assert not thread.is_alive()

def test_add_task_over_max_size_raises_runtime_error() -> None:
    """Adding a task when the maximum pool size is reached must raise ``RuntimeError``."""

    # ARRANGE: Create a pool with size 1 and fill it
    pool = concurrency.TaskPool(max_size=1)

    def dummy_task(event: concurrency.TaskEvent) -> None:
        pass

    pool.add_task(dummy_task)

    # ACT & ASSERT: Attempting to add a second task should raise a ``RuntimeError``
    with pytest.raises(RuntimeError, match="Maximum number of threads reached"):
        pool.add_task(dummy_task)


# =============================================================================
# Tests: concurrency.TaskPool.start_all (Starting registered threads)
# =============================================================================

def test_start_all_starts_inactive_threads() -> None:
    """Starting the pool must clear the stop event and start all inactive threads."""

    # ARRANGE: Create a pool, set the stop event, and add a test task
    pool = concurrency.TaskPool()
    pool._stop_event.set()

    event_cleared_during_task = False

    def task(evt: concurrency.TaskEvent) -> None:
        nonlocal event_cleared_during_task
        event_cleared_during_task = not evt.is_set()

    pool.add_task(task)

    # ACT: Start all tasks in the pool
    pool.start_all()

    # ASSERT: The thread should process successfully with a cleared stop event
    thread = list(pool._threads.keys())[0]
    thread.join()

    assert event_cleared_during_task is True


# =============================================================================
# Tests: concurrency.TaskPool.wait_all (Waiting for threads)
# =============================================================================

def test_wait_all_blocks_until_threads_complete() -> None:
    """Waiting for all tasks must block execution until every registered thread has finished."""

    # ARRANGE: Add a task that sleeps briefly
    pool = concurrency.TaskPool()
    started = concurrency.TaskEvent()

    def task(evt: concurrency.TaskEvent) -> None:
        started.set()
        time.sleep(0.05)

    pool.add_task(task)
    pool.start_all()
    started.wait()

    # ACT: Wait until all threads complete
    pool.wait_all()

    # ASSERT: The registered thread should be fully terminated
    thread = list(pool._threads.keys())[0]

    assert not thread.is_alive()


# =============================================================================
# Tests: concurrency.TaskPool.stop (Cooperative cancellation)
# =============================================================================

def test_stop_sets_stop_event_flag() -> None:
    """Stopping the pool must set the shared stop event flag to signal cooperative cancellation."""

    # ARRANGE: Create a pool and verify the stop event is clear
    pool = concurrency.TaskPool()
    assert not pool._stop_event.is_set()

    # ACT: Send the stop signal
    pool.stop()

    # ASSERT: The stop event flag should be set
    assert pool._stop_event.is_set()


# =============================================================================
# Tests: concurrency.TaskPool.return_all (Collecting results)
# =============================================================================

def test_return_all_yields_task_results_in_order() -> None:
    """Returning all tasks must stop and join threads, yielding their results in registration order."""

    # ARRANGE: Add two distinct tasks to the pool
    pool = concurrency.TaskPool()

    def task1(evt: concurrency.TaskEvent) -> str:
        return "result1"

    def task2(evt: concurrency.TaskEvent) -> str:
        return "result2"

    pool.add_task(task1)
    pool.add_task(task2)
    pool.start_all()

    # ACT: Return all processed results
    results = list(pool.return_all())

    # ASSERT: Verify that both items are returned matching the registration order
    assert len(results) == 2
    assert results[0].result == "result1"
    assert results[1].result == "result2"

def test_return_all_with_timeout_records_timeout_error() -> None:
    """Returning all tasks with a thread exceeding timeout must record a ``TimeoutError`` for that task."""

    # ARRANGE: Start a long-running task
    pool = concurrency.TaskPool()

    def slow_task(evt: concurrency.TaskEvent) -> None:
        time.sleep(0.5)

    pool.add_task(slow_task)
    pool.start_all()

    # ACT: Return tasks with a short expiration timeout
    results = list(pool.return_all(0.01))

    # ASSERT: Verify standard shutdown failed and recorded a ``TimeoutError``
    assert len(results) == 1
    assert isinstance(results[0].exception, TimeoutError)


# =============================================================================
# Tests: concurrency.TaskPool.errors (Exception collection)
# =============================================================================

def test_errors_returns_all_recorded_exceptions() -> None:
    """Accessing errors must return a list of all exceptions encountered by completed tasks."""

    # ARRANGE: Register a failing task and execute the pool
    pool = concurrency.TaskPool()

    def task_with_error(evt: concurrency.TaskEvent) -> None:
        raise ValueError("boom")

    pool.add_task(task_with_error)
    pool.start_all()
    list(pool.return_all())

    # ACT: Query any recorded error exceptions
    errors = pool.errors

    # ASSERT: The collected errors list should contain the respective internal error
    assert len(errors) == 1
    assert isinstance(errors[0], ValueError)
    assert str(errors[0]) == "boom"


# =============================================================================
# Tests: concurrency.TaskPool context manager (Context manager protocol)
# =============================================================================

def test_context_manager_starts_tasks_on_enter() -> None:
    """Entering the ``concurrency.TaskPool`` context must start all registered tasks automatically."""

    # ARRANGE: Create a dummy task
    pool = concurrency.TaskPool()
    task_ran = False

    def task(evt: concurrency.TaskEvent) -> None:
        nonlocal task_ran
        task_ran = True

    pool.add_task(task)

    # ACT: Enter the pool execution context manager
    with pool:
        pass

    # ASSERT: The inner block variables should indicate complete processing
    assert task_ran is True

def test_context_manager_raises_exception_group_on_exit_errors() -> None:
    """Exiting the ``concurrency.TaskPool`` context with task errors must raise an ``ExceptionGroup`` containing the errors."""

    # ARRANGE: Register a failing task to test exception extraction
    pool = concurrency.TaskPool()

    def task(evt: concurrency.TaskEvent) -> None:
        raise KeyError("err")

    pool.add_task(task)

    # ACT & ASSERT: Expected failure extraction on pool termination
    with pytest.raises(ExceptionGroup) as exc_info:
        with pool:
            pass

    assert len(exc_info.value.exceptions) == 1
    assert isinstance(exc_info.value.exceptions[0], KeyError)
    assert str(exc_info.value.exceptions[0]) == "'err'"

def test_taskpool_iterator_yields_tasks() -> None:
    """Iterating over a ``concurrency.TaskPool`` must yield the remaining tasks."""

    # ARRANGE: Add a few tasks to the pool
    pool = concurrency.TaskPool()

    def task1(evt: concurrency.TaskEvent) -> None: pass
    def task2(evt: concurrency.TaskEvent) -> None: pass

    pool.add_task(task1)
    pool.add_task(task2)

    # ACT: Evaluate iteration over the object
    items = list(pool)

    # ASSERT: Should directly yield tasks remaining in the underlying mapping
    assert len(items) == 2
    for item in items:
        assert isinstance(item, concurrency.Task)
