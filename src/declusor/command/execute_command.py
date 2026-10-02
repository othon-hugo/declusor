from dataclasses import dataclass

from declusor import config, contract
from declusor.command.base import BaseStreamCommand


@dataclass(frozen=True)
class ExecuteCommandDTO:
    """Data transfer object containing parameters for remote command execution.

    Encapsulates and validates the raw command line string to be transmitted
    and executed on the remote client.

    Raises:
        InvalidOperation: If ``command_line`` is empty or consists solely of whitespace.
    """

    command_line: str
    """command_line: Non-empty shell command line string."""

    def __post_init__(self) -> None:
        if not self.command_line or not self.command_line.strip():
            raise config.InvalidOperation("Command line cannot be empty.")


class ExecuteCommand(BaseStreamCommand):
    """Execute a raw shell command string on the remote client.

    Transmits the encoded command string encapsulated in an ``ExecuteCommandDTO``
    through the active session connection and streams all response chunks directly
    to the operator's console.
    """

    def __init__(self, dto: ExecuteCommandDTO, /) -> None:
        """Initialize ExecuteCommand with validated parameters.

        Args:
            dto: Validated data transfer object containing the command string.
        """

        super().__init__()
        self._dto = dto

    def send_request(self, session: contract.SessionContext, /) -> None:
        """Send the encoded command string to the remote client.

        Args:
            session: The active session providing connection transport.

        Raises:
            ConnectionClosed: If the connection is not in OPEN state.
            ConnectionWriteError: If the socket write operation fails.
        """

        session.connection.write(self._payload(session))

    def _payload(self, session: contract.SessionContext, /) -> bytes:
        rendered = session.connection.renderer.render_operation_command(
            config.OperationCode.EXEC_COMMAND,
            self._dto.command_line,
        )

        if rendered:
            return rendered.encode()

        return self._dto.command_line.encode()
