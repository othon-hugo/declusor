from typing import Any

from declusor import interface


class MockCommand(interface.ICommand):
    """A mock implementation of ICommand for testing."""

    def __init__(self, *args: "Any", **kwargs: "Any") -> None:
        self.init_args = args
        self.init_kwargs = kwargs
        self.execute_called_with: list[tuple["interface.IConnection", "interface.IConsole"]] = []

    def execute(self, connection: "interface.IConnection", console: "interface.IConsole", /) -> None:
        self.execute_called_with.append((connection, console))
