from dataclasses import dataclass

from declusor import config, contract


@dataclass(frozen=True)
class ExecuteCommandDTO:
    """Data transfer object containing parameters for remote command execution.

    Encapsulates and validates the raw command line string to be transmitted
    and executed on the remote client.

    Attributes:
        command_line: Non-empty shell command line string.

    Raises:
        InvalidOperation: If ``command_line`` is empty or consists solely of whitespace.
    """

    command_line: str

    def __post_init__(self) -> None:
        if not self.command_line or not self.command_line.strip():
            raise config.InvalidOperation("Command line cannot be empty.")


class ExecuteCommand(contract.ICommand):
    """Execute a raw shell command string on the remote client.

    Transmits the encoded command string encapsulated in an ``ExecuteCommandDTO``
    through the active session connection and streams all response chunks directly
    to the operator's console.

    Attributes:
        dto: The validated parameters for this command.
    """

    def __init__(self, dto: ExecuteCommandDTO) -> None:
        """Initialize ExecuteCommand with validated parameters.

        Args:
            dto: Validated data transfer object containing the command string.
        """

        super().__init__()

        self._dto = dto
        self._command_line = dto.command_line.encode()

    @property
    def dto(self) -> ExecuteCommandDTO:
        """The command parameters."""

        return self._dto

    def send_request(self, session: contract.SessionContext) -> None:
        """Send the encoded command string to the remote client.

        Args:
            session: The active session providing connection transport.

        Raises:
            ConnectionClosed: If the connection is not in OPEN state.
            ConnectionWriteError: If the socket write operation fails.
        """

        session.connection.write(self._command_line)

    def read_response(self, session: contract.SessionContext) -> None:
        """Read output chunks from the remote client and display them on the console.

        Args:
            session: The active session providing connection and console interfaces.

        Raises:
            ConnectionClosed: If the remote peer terminates the connection unexpectedly.
        """

        for data in session.connection.read():
            session.console.write_binary_data(data)
