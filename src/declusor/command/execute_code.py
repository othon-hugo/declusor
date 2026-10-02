from dataclasses import dataclass

from declusor import config, contract
from declusor.command.base import BaseStreamCommand


@dataclass(frozen=True)
class ExecuteCodeDTO:
    """Data transfer object containing parameters for native client code execution.

    Encapsulates and validates the raw code string to be evaluated directly by
    the remote client agent's runtime.

    Raises:
        InvalidOperation: If ``code`` is empty or consists solely of whitespace.
    """

    code: str
    """Non-empty code string to evaluate."""

    def __post_init__(self) -> None:
        if not self.code or not self.code.strip():
            raise config.CommandValidationError("Code cannot be empty.", field="code", value=self.code)


class ExecuteCode(BaseStreamCommand):
    """Execute raw native client runtime code on the remote client.

    Transmits the encoded code string encapsulated in an ``ExecuteCodeDTO``
    through the active session connection and streams all response chunks directly
    to the operator's console.
    """

    def __init__(self, dto: ExecuteCodeDTO, /) -> None:
        """Initialize ExecuteCode with validated parameters.

        Args:
            dto: Validated data transfer object containing the code string.
        """

        super().__init__()
        self._dto = dto

    def send_request(self, session: contract.SessionContext, /) -> None:
        """Send the rendered or raw code string to the remote client.

        Args:
            session: The active session providing connection transport and profile.

        Raises:
            ConnectionClosed: If the connection is not in OPEN state.
            ConnectionWriteError: If the socket write operation fails.
        """

        session.connection.write(self._payload(session))

    def _payload(self, session: contract.SessionContext, /) -> bytes:
        rendered = session.connection.renderer.render_operation_command(
            config.OperationCode.EXEC_CODE,
            self._dto.code,
        )

        if rendered:
            return rendered.encode()

        return self._dto.code.encode()
