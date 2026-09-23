from declusor import config, contract
from declusor.command.dto import LoadModuleDTO


class LoadModule(contract.ICommand):
    """Load an operator-selected module into the remote client.

    Retrieves module payload from the active session's client file store,
    transmits the module definition across the network connection, and
    displays the resulting client response on the operator console.

    Attributes:
        dto: The validated parameters for this module load command.
    """

    def __init__(self, dto: LoadModuleDTO) -> None:
        """Initialize LoadModule with validated module parameters.

        Args:
            dto: Validated DTO containing the clean module identifier.
        """

        super().__init__()

        self._dto = dto
        self._module_name = dto.module_name

    @property
    def dto(self) -> LoadModuleDTO:
        """The command parameters."""

        return self._dto

    def send_request(self, session: contract.SessionContext) -> None:
        """Send the resolved module script to the remote client.

        Args:
            session: Active session providing connection transport and file store.

        Raises:
            CommandError: If the session file store is unavailable.
            ModuleNotFound: If the requested module file cannot be found.
            ConnectionClosed: If the connection is closed.
            ConnectionWriteError: If transmitting the module payload fails.
        """

        if session.files is None:
            raise config.CommandError("Client file store is not configured for this session.")

        module_bytes = session.files.load_module(self._module_name)
        session.connection.write(module_bytes)

    def read_response(self, session: contract.SessionContext) -> None:
        """Read and display the remote client's module registration response.

        Args:
            session: Active session providing connection and console interfaces.

        Raises:
            ConnectionClosed: If the remote peer terminates the connection unexpectedly.
        """

        for data in session.connection.read():
            session.console.write_binary_data(data)
