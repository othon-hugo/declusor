from __future__ import annotations

import time
from collections.abc import Callable, Sequence

from declusor import contract, util

from .view import DummyView


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


class DisconnectAwareInputSource(DummyInputSource):
    """Input source double that yields queued commands and unblocks on cooperative stop flag."""

    def __init__(
        self,
        inputs: Sequence[str] | None = None,
        *,
        stop_event: util.TaskEvent | None = None,
        timeout: float = 3.0,
        input_exception: BaseException | None = None,
    ) -> None:
        """Initialize the disconnect-aware input source double.

        Args:
            inputs: Initial sequence of input strings.
            stop_event: Cooperative task stop event to await when inputs are exhausted.
            timeout: Maximum wait time in seconds before raising TimeoutError.
            input_exception: Optional exception to raise on first read invocation.
        """

        super().__init__(inputs)
        self._stop_event = stop_event
        self._timeout = timeout
        self.input_exception = input_exception

    def read_raw(self, prompt: str = "", /) -> str:
        """Return next input or wait for cooperative stop event before returning empty string.

        Args:
            prompt: Optional command prompt string.

        Returns:
            Next raw input line or empty string upon stop event signal.

        Raises:
            TimeoutError: If stop_event wait exceeds timeout.
            EOFError: If input is exhausted and no stop_event is provided.
        """

        self.prompts.append(prompt)

        if self.input_exception is not None:
            exc = self.input_exception
            self.input_exception = None
            raise exc

        if self._inputs:
            line = self._inputs.pop(0)

            return line if line.endswith("\n") else f"{line}\n"

        if self._stop_event is not None:
            if not self._stop_event.wait(timeout=self._timeout):
                raise TimeoutError(f"Timed out waiting {self._timeout}s for stop event.")

            return ""

        raise EOFError("No further input available and no stop event registered.")


class PacedInteractiveInputSource(DummyInputSource):
    """Input source double that paces queued commands against view output reception."""

    def __init__(
        self,
        interactions: Sequence[tuple[str, bytes]],
        view: DummyView,
        *,
        is_idle_predicate: Callable[[], bool] | None = None,
        terminal_exception: BaseException | None = None,
        timeout: float = 3.0,
    ) -> None:
        """Initialize the paced interactive input source double.

        Args:
            interactions: Sequence of (command_to_send, expected_output_bytes) tuples.
            view: Captured view double whose binary output is inspected.
            is_idle_predicate: Optional callable returning True when the connection is idle.
            terminal_exception: Exception to raise when interactions are exhausted.
            timeout: Maximum wait time in seconds for expected view output.
        """

        super().__init__()
        self._interactions: list[tuple[str, bytes]] = list(interactions)
        self._view = view
        self._is_idle_predicate = is_idle_predicate
        self._terminal_exception: BaseException = terminal_exception if terminal_exception is not None else KeyboardInterrupt()
        self._timeout = timeout
        self._last_expected: bytes | None = None
        self._view_cursor: int = 0

    def read_raw(self, prompt: str = "", /) -> str:
        """Pace command submission against previous response reception before yielding next command.

        Args:
            prompt: Optional command prompt string.

        Returns:
            Next command line.

        Raises:
            BaseException: Configured terminal exception when all interactions are processed.
            TimeoutError: If expected view output is not observed before timeout.
        """

        self.prompts.append(prompt)

        if self.input_exception is not None:
            exc = self.input_exception
            self.input_exception = None
            raise exc

        if self._last_expected is not None:
            self._wait_for_view_content(self._last_expected)
            self._last_expected = None

        if self._interactions:
            cmd, expected = self._interactions.pop(0)
            self._last_expected = expected

            return cmd if cmd.endswith("\n") else f"{cmd}\n"

        raise self._terminal_exception

    def _wait_for_view_content(self, expected: bytes) -> None:
        """Wait for expected byte sequence to appear in view binary output while connection is idle.

        Args:
            expected: Byte sequence expected in newly captured view output.

        Raises:
            TimeoutError: If expected view output is not observed before timeout.
        """

        deadline = time.monotonic() + self._timeout
        while time.monotonic() < deadline:
            accumulated = b"".join(self._view.binary_data[self._view_cursor :])
            idle = self._is_idle_predicate() if self._is_idle_predicate is not None else True
            if expected in accumulated and idle:
                self._view_cursor = len(self._view.binary_data)

                return

            time.sleep(0.005)

        raise TimeoutError(f"Timed out waiting for expected view output: {expected!r}")
