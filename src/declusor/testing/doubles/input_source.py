from collections.abc import Sequence

from declusor import contract


class DummyInputSource(contract.IInputSource):
    """Fully-typed in-memory input source simulating operator input."""

    def __init__(self, inputs: Sequence[str] | None = None) -> None:
        self._inputs: list[str] = list(inputs) if inputs is not None else []
        self.input_exception: BaseException | None = None
        self.prompts: list[str] = []

    def feed_inputs(self, *lines: str) -> None:
        """Enqueue simulated input lines for read_command and read_raw."""

        self._inputs.extend(lines)

    def read_command(self, prompt: str = "", /) -> str:
        """Return the next queued stripped input line or empty string if queue is empty."""

        self.prompts.append(prompt)

        if self.input_exception is not None:
            exc = self.input_exception
            self.input_exception = None
            raise exc

        if not self._inputs:
            return ""

        return self._inputs.pop(0).strip()

    def read_raw(self, prompt: str = "", /) -> str:
        """Return the next queued input line or newline if queue is empty."""

        self.prompts.append(prompt)

        if self.input_exception is not None:
            exc = self.input_exception
            self.input_exception = None
            raise exc

        if not self._inputs:
            return "\n"

        line = self._inputs.pop(0)

        return line if line.endswith("\n") else f"{line}\n"
