from unittest.mock import MagicMock

from declusor import contract


class DummyCommand(contract.ICommand):
    """Test command tracking execution call sequence."""

    def __init__(self) -> None:
        super().__init__()
        self.call_sequence: list[str] = []

    def send_request(self, session: contract.SessionContext) -> None:
        self.call_sequence.append("send_request")

    def read_response(self, session: contract.SessionContext) -> None:
        self.call_sequence.append("read_response")


def test_command_execute_runs_send_request_before_read_response() -> None:
    """ICommand.execute must invoke send_request before read_response."""
    session = contract.SessionContext(
        connection=MagicMock(spec=contract.IConnection),
        console=MagicMock(spec=contract.IConsole),
        files=MagicMock(spec=contract.IClientFileStore),
    )

    command = DummyCommand()
    session.execute(command)

    assert command.call_sequence == ["send_request", "read_response"]
