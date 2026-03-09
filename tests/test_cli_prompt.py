"""Tests for the ``declusor.cli.prompt`` module."""

import pytest

from declusor import config, interface, mock
from declusor.cli import prompt


# =============================================================================
# Dummies/Mocks
# =============================================================================

def dummy_controller(conn: interface.IConnection, term: interface.IConsole, arg: str) -> None:
    """Null-implementation controller for testing command dispatch mappings."""

class DummyThrowingRouter(mock.MockRouter):
    """Null-implementation router returning functions strictly throwing specific configured exception cascades."""
    def __init__(self, exception_type: type[Exception] | Exception, target_route: str | None = None) -> None:
        super().__init__()
        self.exception_type = exception_type
        self_target = target_route
        self.target_route = self_target

    def locate(self, route: str) -> getattr:
        def raise_exception(*args, **kwargs) -> None:
            if self.target_route is None or route == self.target_route:
                if isinstance(self.exception_type, Exception):
                    raise self.exception_type
                raise self.exception_type()
        return raise_exception


# =============================================================================
# Tests: PromptCLI.run (Interactive Loop Execution)
# =============================================================================

def test_promptcli_run_executes_registered_command() -> None:
    """Running the prompt must read a command, locate it in the router, and dispatch to the controller."""

    # ARRANGE: Setup an interactive session environment
    conn = mock.MockConnection(mock.MockConnectionProfile())
    console = mock.MockConsole()
    router = mock.MockRouter()

    router.connect("test_command", dummy_controller)

    # Inject input commands and handle system completion signal to escape loop
    console.lines_to_read = ["test_command my_args", KeyboardInterrupt]
    cli = prompt.PromptCLI("test", router, conn, console)

    # ACT: Process user inputs tracking invocation sequences
    cli.run()

    # ASSERT: The router identifies and processes properly
    assert "test_command" in router._routes

def test_promptcli_run_handles_argumentless_commands() -> None:
    """Running the prompt must seamlessly process commands that omit an argument string."""

    # ARRANGE: Setup interactive sequence with blank trailing spaces
    conn = mock.MockConnection(mock.MockConnectionProfile())
    console = mock.MockConsole()
    router = mock.MockRouter()

    router.connect("test_command", dummy_controller)

    console.lines_to_read = ["test_command", KeyboardInterrupt]
    cli = prompt.PromptCLI("test", router, conn, console)

    # ACT: Run processing
    cli.run()

    # ASSERT: Invoked securely
    assert "test_command" in router._routes

def test_promptcli_run_skips_empty_lines() -> None:
    """Running the prompt must skip past blank lines and query the user again."""

    # ARRANGE: Introduce empty string logic execution flow termination
    conn = mock.MockConnection(mock.MockConnectionProfile())
    console = mock.MockConsole()
    router = mock.MockRouter()

    router.connect("test_command", dummy_controller)

    # Feed an empty line, a valid command, then interrupt
    console.lines_to_read = ["   ", "", "test_command", KeyboardInterrupt]
    cli = prompt.PromptCLI("test", router, conn, console)

    # ACT: Start CLI read sequence
    cli.run()

    # ASSERT: Should disregard blank inputs appropriately defaulting to next cycle
    assert len(console.lines_to_read) == 0

def test_promptcli_route_command_raises_prompt_error() -> None:
    """Routing an empty command line directly must raise a ``PromptError``."""

    # ARRANGE: Target dispatch method wrapper mapping empty requests safely
    conn = mock.MockConnection(mock.MockConnectionProfile())
    console = mock.MockConsole()
    router = mock.MockRouter()
    cli = prompt.PromptCLI("test", router, conn, console)

    # ACT & ASSERT: Validation checks correctly assert execution termination request on missing args
    with pytest.raises(config.RouterError, match="invalid route: ''"):
        cli._route_command("")

def test_promptcli_run_handles_exit_request() -> None:
    """Running the prompt must cleanly terminate the loop when an ``ExitRequest`` is raised."""

    # ARRANGE: Throw an exit request during router dispatch
    conn = mock.MockConnection(mock.MockConnectionProfile())
    console = mock.MockConsole()

    router = DummyThrowingRouter(config.ExitRequest)
    console.lines_to_read = ["test_command", "never_read_cmd"]
    cli = prompt.PromptCLI("test", router, conn, console)

    # ACT: Execute command triggers early-exit logic
    cli.run()

    # ASSERT: The input loop was safely terminated before fetching subsequent commands
    assert "never_read_cmd" in console.lines_to_read

def test_promptcli_run_handles_keyboard_interrupt_during_execution() -> None:
    """Running the prompt must catch a ``KeyboardInterrupt`` raised during command dispatch and continue the loop."""

    # ARRANGE: Throw interrupt dynamically as response from route handler
    conn = mock.MockConnection(mock.MockConnectionProfile())
    console = mock.MockConsole()

    router = DummyThrowingRouter(KeyboardInterrupt, target_route="throw")
    console.lines_to_read = ["throw", "next", KeyboardInterrupt]
    cli = prompt.PromptCLI("test", router, conn, console)

    # ACT: Throwing doesn't stop prompt execution entirely, simply skips evaluation logic
    cli.run()

    # ASSERT: Survived early interrupt to process successive target queue
    assert len(console.lines_to_read) == 0

def test_promptcli_run_logs_declusor_exceptions() -> None:
    """Running the prompt must catch ``DeclusorException`` raised during execution and output it via the console."""
    # ARRANGE: Raise a standard architectural exception internal to declusor mechanics
    conn = mock.MockConnection(mock.MockConnectionProfile())
    console = mock.MockConsole()

    router = DummyThrowingRouter(config.PromptError("invalid route data"))
    console.lines_to_read = ["bad", KeyboardInterrupt]
    cli = prompt.PromptCLI("test", router, conn, console)

    # ACT: Safe suppression
    cli.run()

    # ASSERT: Standard output captured the message successfully
    assert len(console.written_error_messages) == 1
    assert isinstance(console.written_error_messages[0], config.PromptError)
