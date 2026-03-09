from typing import Any


class MockEvent:
    def __init__(self, side_effect: list[bool]) -> None:
        self._returns = side_effect

    def is_set(self) -> bool:
        if self._returns:
            return self._returns.pop(0)
        return True

    def set(self) -> None:
        pass


class MockTaskPool:
    def __init__(self) -> None:
        self.tasks: list[Any] = []
        self.started = False
        self.waited = False
        self.stopped = False

    def add_task(self, handler: Any) -> None:
        self.tasks.append(handler)

    def start_all(self) -> None:
        self.started = True

    def wait_all(self) -> None:
        self.waited = True

    def stop(self) -> None:
        self.stopped = True
