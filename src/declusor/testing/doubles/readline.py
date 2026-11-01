"""In-memory readline test double for deterministic terminal and completion testing."""

from collections.abc import Callable

from declusor import contract


class DummyReadlineAdapter(contract.IReadlineAdapter):
    """Configurable in-memory readline adapter double."""

    def __init__(
        self,
        is_available: bool = True,
        line_buffer: str = "",
        read_error: Exception | None = None,
        write_error: Exception | None = None,
        line_buffer_error: Exception | None = None,
    ) -> None:
        """Initialize test double with configurable initial state and simulated errors."""

        self.is_available_flag: bool = is_available
        self.line_buffer: str = line_buffer
        self.read_error: Exception | None = read_error
        self.write_error: Exception | None = write_error
        self.line_buffer_error: Exception | None = line_buffer_error

        self.completer: Callable[[str, int], str | None] | None = None
        self.completer_delims: str = ""
        self.bindings: list[str] = []
        self.read_paths: list[str] = []
        self.written_paths: list[str] = []

    @property
    def is_available(self) -> bool:
        """Return True when readline capability is simulated as available."""

        return self.is_available_flag

    @is_available.setter
    def is_available(self, value: bool) -> None:
        """Allow dynamically toggling availability."""

        self.is_available_flag = value

    def get_line_buffer(self) -> str:
        """Return configured line buffer or raise simulated error."""

        if self.line_buffer_error is not None:
            raise self.line_buffer_error

        return self.line_buffer

    def get_completer(self) -> Callable[[str, int], str | None] | None:
        """Return the registered completer callback."""

        return self.completer

    def get_completer_delims(self) -> str:
        """Return the word delimiters used for tab completion."""

        return self.completer_delims

    def set_completer(self, completer: Callable[[str, int], str | None] | None = None, /) -> None:
        """Record the registered completer callback."""

        self.completer = completer

    def set_completer_delims(self, string: str, /) -> None:
        """Record the registered completer delimiters."""

        self.completer_delims = string

    def parse_and_bind(self, line: str, /) -> None:
        """Record a readline initialization binding."""

        self.bindings.append(line)

    def read_history_file(self, filename: str, /) -> None:
        """Record read history path or raise simulated error."""

        if self.read_error is not None:
            raise self.read_error

        self.read_paths.append(filename)

    def write_history_file(self, filename: str, /) -> None:
        """Record written history path or raise simulated error."""

        if self.write_error is not None:
            raise self.write_error

        self.written_paths.append(filename)
