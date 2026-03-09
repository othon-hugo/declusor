from typing import Generic, TypeVar

from declusor import interface


T = TypeVar("T")


class MockParser(interface.IParser[T], Generic[T]):
    """A mock implementation of IParser for testing."""

    def __init__(self, parse_result: T) -> None:
        self.parse_result = parse_result

    def parse(self) -> T:
        return self.parse_result
