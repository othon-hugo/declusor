"""Mock implementation of the pathlib.Path interface for testing without disk I/O."""

from typing import Any, Self


class MockPath:
    """A mock implementation of a pathlib.Path object for testing."""

    def __init__(self, exists: bool = True, is_file: bool = True, read_data: str | bytes = "data", error: Exception | None = None) -> None:
        self._exists = exists
        self._is_file = is_file
        self.read_data = read_data
        self.error = error

    def exists(self) -> bool:
        return self._exists

    def is_file(self) -> bool:
        return self._is_file

    def open(self, mode: str = "r", encoding: str | None = None) -> Any:
        if self.error:
            raise self.error

        class MockFile:
            def __init__(self, data: str | bytes) -> None:
                self.data = data

            def __enter__(self) -> Self:
                return self

            def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
                pass

            def read(self) -> str | bytes:
                return self.data

        return MockFile(self.read_data)

    def resolve(self) -> Self:
        return self
