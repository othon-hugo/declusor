import time

import pytest

from declusor.util import concurrency


class TestTaskEvent:
    """Verify TaskEvent primitive behavior."""

    def test_task_event_init__default_state__is_unset(self) -> None:
        """Verify TaskEvent initializes in an unset state."""

        event = concurrency.TaskEvent()

        assert not event.is_set()


class TestTask:
    """Verify Task dataclass initialization and field storage."""

    def test_task_dataclass_init__default_fields__are_none(self) -> None:
        """Verify Task dataclass initializes with None for result and exception."""

        task = concurrency.Task()

        assert task.result is None
        assert task.exception is None

    def test_task_dataclass_init__custom_fields__stores_result_and_exception(self) -> None:
        """Verify Task dataclass preserves explicitly supplied result and exception."""

        err = ValueError("test failure")
        task = concurrency.Task(result=123, exception=err)

        assert task.result == 123
        assert task.exception is err


class TestTaskPoolInit:
    """Verify TaskPool configuration and default values."""

    def test_task_pool_init__default_arguments__sets_defaults(self) -> None:
        """Verify TaskPool initializes with default configuration."""

        pool = concurrency.TaskPool()

        assert pool._daemon_mode is True
        assert pool._max_size == 10
        assert not pool._stop_event.is_set()
        assert pool.errors == []

    def test_task_pool_init__custom_stop_event__stores_injected_event(self) -> None:
        """Verify TaskPool accepts and retains an externally injected TaskEvent."""

        custom_event = concurrency.TaskEvent()
        custom_event.set()
        pool = concurrency.TaskPool(stop_event=custom_event)

        assert pool._stop_event is custom_event
        assert pool._stop_event.is_set()

    def test_task_pool_init__daemon_mode_false__creates_non_daemon_threads(self) -> None:
        """Verify daemon_mode=False causes created threads to be non-daemon."""

        pool = concurrency.TaskPool(daemon_mode=False)
        pool.add_task(lambda _: None, name="non-daemon-worker")

        thread = next(iter(pool._threads))
        assert thread.daemon is False


class TestTaskPoolAddTask:
    """Verify TaskPool.add_task task registration and capacity limits."""

    def test_task_pool_add_task__valid_callable__registers_thread_and_task(self) -> None:
        """Verify add_task registers an unstarted thread mapped to a Task object."""

        pool = concurrency.TaskPool()
        pool.add_task(lambda _: 42)

        assert len(pool._threads) == 1
        thread, task = next(iter(pool._threads.items()))
        assert not thread.is_alive()
        assert isinstance(task, concurrency.Task)
        assert task.result is None

    def test_task_pool_add_task__custom_name__assigns_name_to_underlying_thread(self) -> None:
        """Verify add_task assigns the specified thread name."""

        pool = concurrency.TaskPool()
        pool.add_task(lambda _: None, name="worker-special")

        thread = next(iter(pool._threads))
        assert thread.name == "worker-special"

    def test_task_pool_add_task__pool_at_max_size__raises_runtime_error(self) -> None:
        """Verify add_task raises RuntimeError when the pool reaches max_size."""

        pool = concurrency.TaskPool(max_size=2)
        pool.add_task(lambda _: None)
        pool.add_task(lambda _: None)

        with pytest.raises(RuntimeError, match="Maximum number of threads reached"):
            pool.add_task(lambda _: None)

    def test_task_pool_add_task__max_size_zero__raises_runtime_error_immediately(self) -> None:
        """Verify add_task raises RuntimeError immediately when max_size is zero."""

        pool = concurrency.TaskPool(max_size=0)

        with pytest.raises(RuntimeError, match="Maximum number of threads reached"):
            pool.add_task(lambda _: None)


class TestTaskPoolLifecycle:
    """Verify TaskPool start, wait, and stop lifecycle coordination."""

    def test_task_pool_start_all__unstarted_threads__starts_all_registered_threads(self) -> None:
        """Verify start_all transitions registered threads to active running state."""

        ready_event = concurrency.TaskEvent()
        pool = concurrency.TaskPool()

        def task_fn(stop_event: concurrency.TaskEvent) -> None:
            ready_event.wait(timeout=1.0)

        pool.add_task(task_fn, name="worker-start")
        pool.start_all()

        try:
            thread = next(iter(pool._threads))
            assert thread.is_alive()
        finally:
            ready_event.set()
            pool.wait_all()

    def test_task_pool_start_all__already_running_threads__is_idempotent(self) -> None:
        """Verify calling start_all multiple times is idempotent and does not raise."""

        ready_event = concurrency.TaskEvent()
        pool = concurrency.TaskPool()

        def task_fn(stop_event: concurrency.TaskEvent) -> None:
            ready_event.wait(timeout=1.0)

        pool.add_task(task_fn)
        pool.start_all()

        try:
            pool.start_all()
        finally:
            ready_event.set()
            pool.wait_all()

    def test_task_pool_start_all__previously_set_stop_event__clears_event(self) -> None:
        """Verify start_all clears the stop event before starting threads."""

        event = concurrency.TaskEvent()
        event.set()
        pool = concurrency.TaskPool(stop_event=event)
        pool.add_task(lambda _: None)

        pool.start_all()
        pool.wait_all()

        assert not event.is_set()

    def test_task_pool_wait_all__running_threads__blocks_until_completion(self) -> None:
        """Verify wait_all blocks until all threads have completed execution."""

        completed = False
        pool = concurrency.TaskPool()

        def slow_task(stop_event: concurrency.TaskEvent) -> None:
            nonlocal completed
            time.sleep(0.02)
            completed = True

        pool.add_task(slow_task)
        pool.start_all()
        pool.wait_all()

        assert completed is True

    def test_task_pool_wait_all__empty_pool__returns_immediately(self) -> None:
        """Verify wait_all on an empty pool executes safely without error."""

        pool = concurrency.TaskPool()
        pool.wait_all()

    def test_task_pool_stop__called__sets_shared_stop_event(self) -> None:
        """Verify stop signals the cooperative cancellation TaskEvent."""

        pool = concurrency.TaskPool()
        assert not pool._stop_event.is_set()

        pool.stop()

        assert pool._stop_event.is_set()


class TestTaskPoolReturnAll:
    """Verify TaskPool.return_all draining, result capture, and timeouts."""

    def test_task_pool_return_all__successful_tasks__yields_completed_tasks_in_order(self) -> None:
        """Verify return_all yields completed tasks and captures results in registration order."""

        pool = concurrency.TaskPool()
        pool.add_task(lambda _: 10, name="task-1")
        pool.add_task(lambda _: 20, name="task-2")
        pool.start_all()
        pool.wait_all()

        tasks = list(pool.return_all())

        assert len(tasks) == 2
        assert tasks[0].result == 10
        assert tasks[0].exception is None
        assert tasks[1].result == 20
        assert tasks[1].exception is None
        assert len(pool._threads) == 0

    def test_task_pool_return_all__task_exception__captures_exception_in_task(self) -> None:
        """Verify return_all records task exceptions into the Task object."""

        pool = concurrency.TaskPool()
        err = ValueError("inner failure")

        def failing_task(stop_event: concurrency.TaskEvent) -> None:
            raise err

        pool.add_task(failing_task)
        pool.start_all()
        pool.wait_all()

        tasks = list(pool.return_all())

        assert len(tasks) == 1
        assert tasks[0].result is None
        assert tasks[0].exception is err

    def test_task_pool_return_all__thread_timeout__records_timeout_error_with_thread_name(self) -> None:
        """Verify return_all sets TimeoutError with thread name when join times out."""

        hang_event = concurrency.TaskEvent()

        def hanging_task(stop_event: concurrency.TaskEvent) -> None:
            hang_event.wait(timeout=1.0)

        pool = concurrency.TaskPool()
        pool.add_task(hanging_task, name="unresponsive-worker")
        pool.start_all()

        try:
            tasks = list(pool.return_all(0.02))
            assert len(tasks) == 1
            assert isinstance(tasks[0].exception, TimeoutError)
            assert "unresponsive-worker" in str(tasks[0].exception)
        finally:
            hang_event.set()
            time.sleep(0.02)

    def test_task_pool_return_all__empty_pool__yields_no_tasks(self) -> None:
        """Verify return_all on an empty pool yields no tasks."""

        pool = concurrency.TaskPool()
        tasks = list(pool.return_all())

        assert tasks == []
        assert pool.errors == []

    def test_task_pool_return_all__called_repeatedly__yields_empty_on_subsequent_calls(self) -> None:
        """Verify subsequent calls to return_all yield no tasks after initial drain."""

        pool = concurrency.TaskPool()
        pool.add_task(lambda _: 99)
        pool.start_all()
        pool.wait_all()

        first_drain = list(pool.return_all())
        second_drain = list(pool.return_all())

        assert len(first_drain) == 1
        assert second_drain == []


class TestTaskPoolErrors:
    """Verify TaskPool.errors property filtering and timing."""

    def test_task_pool_errors__before_return_all__returns_empty_list(self) -> None:
        """Verify errors property is empty before return_all drains results."""

        pool = concurrency.TaskPool()
        pool.add_task(lambda _: 1 / 0)
        pool.start_all()
        pool.wait_all()

        assert pool.errors == []

    def test_task_pool_errors__mixed_task_outcomes__returns_only_captured_exceptions(self) -> None:
        """Verify errors property returns only the non-None exceptions from drained tasks."""

        pool = concurrency.TaskPool()
        err = RuntimeError("worker-b failed")

        pool.add_task(lambda _: "success-a")
        pool.add_task(lambda _: (_ for _ in ()).throw(err))
        pool.add_task(lambda _: "success-c")
        pool.start_all()
        pool.wait_all()

        list(pool.return_all())

        assert pool.errors == [err]


class TestTaskPoolContextManager:
    """Verify TaskPool context manager exception aggregation into ExceptionGroup."""

    def test_task_pool_context_manager__all_tasks_succeed__executes_cleanly(self) -> None:
        """Verify TaskPool context manager executes and drains cleanly when all tasks succeed."""

        executed = False
        pool = concurrency.TaskPool()

        def task_fn(stop_event: concurrency.TaskEvent) -> None:
            nonlocal executed
            executed = True

        pool.add_task(task_fn)

        with pool:
            pool.wait_all()

        assert executed is True
        assert pool.errors == []

    def test_task_pool_context_manager__task_fails__raises_exception_group(self) -> None:
        """Verify TaskPool context manager raises ExceptionGroup on task failure."""

        err = ValueError("failure in pool")
        pool = concurrency.TaskPool()
        pool.add_task(lambda _: (_ for _ in ()).throw(err))

        with pytest.raises(ExceptionGroup) as exc_info:
            with pool:
                pool.wait_all()

        assert exc_info.value.exceptions == (err,)

    def test_task_pool_context_manager__multiple_task_failures__aggregates_all_exceptions_in_group(self) -> None:
        """Verify TaskPool context manager aggregates multiple exceptions into the ExceptionGroup."""

        err1 = ValueError("failure-1")
        err2 = RuntimeError("failure-2")

        pool = concurrency.TaskPool()
        pool.add_task(lambda _: (_ for _ in ()).throw(err1))
        pool.add_task(lambda _: (_ for _ in ()).throw(err2))

        with pytest.raises(ExceptionGroup) as exc_info:
            with pool:
                pool.wait_all()

        assert len(exc_info.value.exceptions) == 2
        assert err1 in exc_info.value.exceptions
        assert err2 in exc_info.value.exceptions

    def test_task_pool_context_manager__outer_exception_with_task_failure__chains_outer_cause(self) -> None:
        """Verify ExceptionGroup chains the outer with-block exception as its cause."""

        task_err = ValueError("task failure")
        outer_err = RuntimeError("outer with-block failure")

        pool = concurrency.TaskPool()
        pool.add_task(lambda _: (_ for _ in ()).throw(task_err))

        with pytest.raises(ExceptionGroup) as exc_info:
            with pool:
                pool.wait_all()
                raise outer_err

        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, RuntimeError)
        assert str(exc_info.value.__cause__) == "outer with-block failure"


class TestTaskPoolIteration:
    """Verify TaskPool __iter__ protocol over active tasks."""

    def test_task_pool_iter__active_tasks__yields_tasks_tuple(self) -> None:
        """Verify __iter__ returns iterator over registered Task instances."""

        pool = concurrency.TaskPool()
        pool.add_task(lambda _: 1)
        pool.add_task(lambda _: 2)

        tasks = list(pool)

        assert len(tasks) == 2
        assert all(isinstance(t, concurrency.Task) for t in tasks)

    def test_task_pool_iter__empty_pool__yields_empty_iterator(self) -> None:
        """Verify __iter__ on an empty pool yields an empty iterator."""

        pool = concurrency.TaskPool()

        assert list(pool) == []
