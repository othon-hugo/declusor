"""Tests for the ``declusor.interface.command`` module."""

import pytest

from declusor import mock
from declusor.interface import command


# =============================================================================
# Dummies/Mocks
# =============================================================================

class DummyCommand(command.ICommand):
    """Null-implementation subclass delegating to the base abstract method."""

    def execute(self, connection: mock.MockConnection, console: mock.MockConsole) -> None:
        super().execute(connection, console)


# =============================================================================
# Tests: ICommand (Interface contract)
# =============================================================================

def test_icommand_execute_raises_not_implemented_error() -> None:
    """Calling the abstract execute method on ``ICommand`` must raise a ``NotImplementedError``."""

    # ARRANGE: Create a conforming subclass that delegates to the base abstract method
    cmd = DummyCommand()

    # ACT & ASSERT: The base implementation explicitly denies invocation
    with pytest.raises(NotImplementedError):
        cmd.execute(mock.MockConnection(mock.MockConnectionProfile()), mock.MockConsole())
