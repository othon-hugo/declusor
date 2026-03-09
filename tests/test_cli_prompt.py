"""Tests for the ``declusor.cli.prompt`` module."""

import pytest

from declusor import config, mock
from declusor.cli import prompt


# =============================================================================
# Tests: PromptCLI.run (Interactive Loop Execution)
# =============================================================================

def test_promptcli_run_executes_registered_command() -> None:
    """Running the prompt must read a command, locate it in the router, and dispatch to the controller."""

    # ARRANGE: Setup an interactive session environment
    conn = mock.MockConnection(mock.MockConnectionProfile())
    console = mock.MockConsole()
    router = mock.MockRouter()

    def dummy_ct(conn, term, arg):
        pass

    router.connect("test_command", dummy_ct)

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

    def dummy_ct(conn, term, arg):
        pass

    router.connect("test_command", dummy_ct)

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

    def dummy_ct(conn, term, arg):
        pass

    router.connect("test_command", dummy_ct)

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

    class ThrowingRouter(mock.MockRouter):
        def locate(self, route: str):
            def raise_exit(*args, **kwargs) -> None:
                raise config.ExitRequest()

            return raise_exit

    router = ThrowingRouter()
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

    class ThrowingRouter(mock.MockRouter):
        def locate(self, route: str):
            def raise_int(*args, **kwargs) -> None:
                if route == "throw":
                    raise KeyboardInterrupt()

            return raise_int

    router = ThrowingRouter()
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

    class ThrowingRouter(mock.MockRouter):
        def locate(self, route: str):
            def raise_declusor(*args, **kwargs) -> None:
                raise config.PromptError("invalid route data")

            return raise_declusor

    router = ThrowingRouter()
    console.lines_to_read = ["bad", KeyboardInterrupt]
    cli = prompt.PromptCLI("test", router, conn, console)

    # ACT: Safe suppression
    cli.run()

    # ASSERT: Standard output captured the message successfully
    assert len(console.written_error_messages) == 1
    assert isinstance(console.written_error_messages[0], config.PromptError)
